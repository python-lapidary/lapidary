import abc
import dataclasses as dc
import enum
import inspect
import uuid
from enum import Enum, unique

import httpx
import pydantic

from ..absent import ABSENT
from ..compat import typing as ty
from ..http_consts import CONTENT_TYPE
from ..types_ import ParamValue, Serializer

if ty.TYPE_CHECKING:
    from .request import RequestBuilder


class RequestPartHandler(abc.ABC):
    @abc.abstractmethod
    def apply(self, builder: 'RequestBuilder', name: str, typ: type, value: ty.Any) -> None:
        pass


class ParamLocation(enum.Enum):
    cookie = 'cookie'
    header = 'header'
    path = 'path'
    query = 'query'


@unique
class ParamStyle(Enum):
    matrix = 'matrix'
    label = 'label'
    form = 'form'
    simple = 'simple'
    spaceDelimited = 'spaceDelimited'
    pipeDelimited = 'pipeDelimited'
    deepObject = 'deepObject'


@dc.dataclass(frozen=True)
class Param( RequestPartHandler,abc.ABC,):
    alias: ty.Optional[str] = dc.field(default=None)

    style: ParamStyle = dc.field(default=ParamStyle.simple)
    explode: ty.Optional[bool] = dc.field(default=None)

    def _get_explode(self) -> bool:
        return self.explode or self.style == ParamStyle.form

    @abc.abstractmethod
    def _apply(self, builder: 'RequestBuilder', name: str, value: ParamValue):
        pass

    def apply(self, builder: 'RequestBuilder', name: str, typ: type, value: ty.Any) -> None:
        if not value:
            return

        value = serialize_param(value, self.style, self._get_explode())
        self._apply(builder, self.alias or name, value)


#  pylint: disable=unused-argument
def serialize_param(value, style: ParamStyle, explode_list: bool) -> ParamValue:
    # TODO handle style
    if value is None:
        return None
    if isinstance(value, str):
        return value
    elif isinstance(value, (pydantic.BaseModel, pydantic.RootModel)):
        return value.model_dump_json()
    elif isinstance(value, ty.Iterable):
        if explode_list:
            # httpx explodes lists, so just pass it thru
            return [
                serialize_singleton(val)
                for val in value
            ]
        else:
            return ','.join([
                serialize_singleton_as_str(val)
                for val in value
            ])
    else:
        return serialize_singleton(value)


def serialize_singleton(value: ty.Any) -> httpx._types.PrimitiveData:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    elif isinstance(value, (
            uuid.UUID,
    )):
        return str(value)
    elif isinstance(value, enum.Enum):
        return value.value

    else:
        raise TypeError(type(value))


def serialize_singleton_as_str(value: ty.Any) -> str:
    if isinstance(value, str):
        return value
    elif isinstance(value, (int, float, bool, uuid.UUID,)):
        return str(value)
    elif isinstance(value, enum.Enum):
        return value.value
    else:
        raise TypeError(type(value))


class AuthHandler(RequestPartHandler):
    def apply(self, builder: 'RequestBuilder', name: str, typ: type, value: ty.Any) -> None:
        builder.auth = value


@dc.dataclass(frozen=True)
class RequestPart:
    request_part: RequestPartHandler
    name: str
    type: type

    def apply(self, builder: 'RequestBuilder', value: ty.Any) -> None:
        if value is not ABSENT:
            self.request_part.apply(builder, self.name, self.type, value)


@dc.dataclass(frozen=True)
class RequestBody(RequestPartHandler):
    content: ty.Mapping[str, ty.Type]

    def apply(self, builder: 'RequestBuilder', name: str, typ: type, value: ty.Any) -> None:
        content_type, serializer = self.find_request_body_serializer(value)
        builder.headers[CONTENT_TYPE] = content_type
        builder.content = serializer(value)

    def find_request_body_serializer(
            self,
            obj: ty.Any,
    ) -> ty.Tuple[str, Serializer]:
        # find the serializer by type

        for content_type, typ in self.content.items():
            if typ == type(obj):
                def serialize(model):
                    return serialize_param(model, ParamStyle.simple, explode_list=False)

                return content_type, serialize

        raise TypeError(f'Unknown serializer for {type(obj)}')


def parse_params(sig: inspect.Signature) -> ty.Mapping[str, RequestPart]:
    result = {}
    for param in sig.parameters.values():
        name_part = parse_param(param)
        if name_part:
            key, value = name_part
            result[key] = value
    return result


def parse_param(param: inspect.Parameter) -> ty.Optional[ty.Tuple[str, RequestPart]]:
    typ = ty.cast(type, param.annotation)
    name = param.name

    if typ == ty.Self:
        return None

    if isinstance(typ, type) and issubclass(typ, httpx.Auth):
        return name, RequestPart(AuthHandler(), name, typ)

    return name, RequestPart(get_handler(name, typ), name, typ)


def get_handler(param_name: str, typ: type) -> RequestPartHandler:
    annos = find_annotations(typ, RequestPartHandler)  # type: ignore[type-abstract]

    if len(annos) != 1:
        raise ValueError(f'{param_name}: expected exactly one Lapidary annotation.')

    return annos[0]


T = ty.TypeVar('T')


def find_annotations(
        user_type: type, annotation_type: type[T], ) -> ty.Sequence[T]:
    if user_type is inspect.Signature.empty or '__metadata__' not in dir(user_type):
        return ()
    return [anno for anno in user_type.__metadata__ if isinstance(anno, annotation_type)]  # type: ignore[attr-defined]
