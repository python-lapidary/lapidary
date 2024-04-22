import abc
import dataclasses as dc
import inspect
from typing import Optional

import pydantic
import typing_extensions as typing

from .._httpx import ParamValue
from ..http_consts import CONTENT_TYPE, MIME_JSON
from .encode_param import Encoder, ParamStyle, get_encode_fn

if typing.TYPE_CHECKING:
    from .request import RequestBuilder


class ParameterAnnotation(abc.ABC):
    @abc.abstractmethod
    def supply_formal(self, name: str, typ: type) -> None:
        pass


class RequestPartHandler(abc.ABC):
    @abc.abstractmethod
    def apply(self, builder: 'RequestBuilder', value: typing.Any) -> None:
        pass


class Param(RequestPartHandler, ParameterAnnotation, abc.ABC):
    name: str
    encoder: typing.Optional[Encoder]

    style: ParamStyle
    alias: typing.Optional[str]
    explode: typing.Optional[bool]

    def __init__(self, alias: Optional[str], /, *, style: ParamStyle, explode: Optional[bool]) -> None:
        self.alias = alias
        self.style = style
        self.explode = explode

    def supply_formal(self, name: str, typ: type) -> None:
        self.name = name
        self.encoder = get_encode_fn(typ, self.style, self._get_explode())
        assert self.encoder

    def _get_explode(self) -> bool:
        return self.explode or self.style == ParamStyle.form

    @abc.abstractmethod
    def _apply(self, builder: 'RequestBuilder', value: ParamValue):
        pass

    def apply(self, builder: 'RequestBuilder', value: typing.Any) -> None:
        if not value:
            return

        assert self.encoder
        value = self.encoder(self.name, value)
        self._apply(builder, value)

    @property
    def http_name(self) -> str:
        return self.alias or self.name

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            raise NotImplementedError
        return self.__dict__ == other.__dict__


@dc.dataclass
class RequestBody(RequestPartHandler, ParameterAnnotation):
    name: str = dc.field(init=False)
    content: typing.Mapping[str, type]
    _serializer: pydantic.TypeAdapter = dc.field(init=False)

    def supply_formal(self, name: str, typ: type) -> None:
        self.name = name
        self._serializer = pydantic.TypeAdapter(typ)

    def apply(self, builder: 'RequestBuilder', value: typing.Any) -> None:
        content_type = self.find_content_type(value)
        builder.headers[CONTENT_TYPE] = content_type

        plain_content_type = content_type[: content_type.index(';')] if ';' in content_type else content_type
        if plain_content_type == MIME_JSON:
            builder.content = self._serializer.dump_json(value, by_alias=True, exclude_defaults=True)
        else:
            raise NotImplementedError(content_type)

    def find_content_type(self, value: typing.Any) -> str:
        for content_type, typ in self.content.items():
            origin_type = typing.get_origin(typ) or typ
            if isinstance(value, origin_type):
                return content_type

        raise ValueError('Could not determine content type')


def process_params(sig: inspect.Signature) -> typing.Mapping[str, ParameterAnnotation]:
    return dict(process_param(param) for param in sig.parameters.values() if param.annotation not in (typing.Self, None))


def process_param(param: inspect.Parameter) -> typing.Tuple[str, ParameterAnnotation]:
    name = param.name
    typ = param.annotation

    annotations = find_annotations(typ, ParameterAnnotation)  # type: ignore[type-abstract]
    if len(annotations) != 1:
        raise ValueError(f'{name}: expected exactly one Lapidary annotation.', typ)
    annotation = annotations[0]
    annotation.supply_formal(name, typ.__origin__)
    return name, annotation


T = typing.TypeVar('T')


def find_annotations(
    user_type: type,
    annotation_type: type[T],
) -> typing.Sequence[T]:
    if user_type is inspect.Signature.empty or '__metadata__' not in dir(user_type):
        return ()
    return [anno for anno in user_type.__metadata__ if isinstance(anno, annotation_type)]  # type: ignore[attr-defined]
