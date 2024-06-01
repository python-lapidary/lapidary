import abc
import dataclasses as dc
import inspect
from typing import TYPE_CHECKING, Callable, Optional

import httpx
import pydantic
import typing_extensions as typing

from ..http_consts import CONTENT_TYPE, MIME_JSON
from .encode_param import ParamStyle, get_encode_fn
from .request import RequestHandler
from .response import ResponseHandler

if TYPE_CHECKING:
    from .._httpx import ParamValue
    from .encode_param import Encoder
    from .request import RequestBuilder


class NameTypeAwareAnnotation(abc.ABC):
    _name: str
    _type: type

    def supply_formal(self, name: str, typ: type) -> None:
        self._name = name
        self._type = typ


@dc.dataclass
class RequestBody(NameTypeAwareAnnotation, RequestHandler):
    content: typing.Mapping[str, type]
    _serializer: Callable[[typing.Any], bytes] = dc.field(init=False)

    def supply_formal(self, name: str, typ: type) -> None:
        super().supply_formal(name, typ)
        self._serializer = lambda content: pydantic.TypeAdapter(typ).dump_json(
            content,
            by_alias=True,
            exclude_unset=True,
        )

    def apply_request(self, builder: 'RequestBuilder', value: typing.Any) -> None:
        content_type = self.find_content_type(value)
        builder.headers[CONTENT_TYPE] = content_type

        plain_content_type = content_type[: content_type.index(';')] if ';' in content_type else content_type
        if plain_content_type == MIME_JSON:
            builder.content = self._serializer(value)
        else:
            raise NotImplementedError(content_type)

    def find_content_type(self, value: typing.Any) -> str:
        for content_type, typ in self.content.items():
            origin_type = typing.get_origin(typ) or typ
            if isinstance(value, origin_type):
                return content_type

        raise ValueError('Could not determine content type')


class ResponseBody(NameTypeAwareAnnotation, ResponseHandler):
    """Annotate response body within an Envelope type."""

    _parse: Callable[[bytes], typing.Any]

    def supply_formal(self, name: str, typ: type) -> None:
        super().supply_formal(name, typ)
        self._parse = pydantic.TypeAdapter(typ).validate_json

    def apply_response(self, response: httpx.Response, fields: typing.MutableMapping) -> None:
        fields[self._name] = self._parse(response.content)


class Param(RequestHandler, NameTypeAwareAnnotation, abc.ABC):
    style: ParamStyle
    alias: typing.Optional[str]
    explode: typing.Optional[bool]
    _encoder: 'typing.Optional[Encoder]'

    def __init__(self, alias: Optional[str], /, *, style: ParamStyle, explode: Optional[bool]) -> None:
        self.alias = alias
        self.style = style
        self.explode = explode
        self._encoder = None

    def _get_explode(self) -> bool:
        return self.explode or self.style == ParamStyle.form

    @abc.abstractmethod
    def _apply_request(self, builder: 'RequestBuilder', value: 'ParamValue'):
        pass

    def apply_request(self, builder: 'RequestBuilder', value: typing.Any) -> None:
        if not value:
            return

        if not self._encoder:
            self._encoder = get_encode_fn(self._type, self.style, self._get_explode())
        assert self._encoder
        value = self._encoder(self._name, value)
        self._apply_request(builder, value)

    @property
    def http_name(self) -> str:
        return self.alias or self._name


T = typing.TypeVar('T')


def find_annotations(
    user_type: type,
    annotation_type: type[T],
) -> typing.Sequence[T]:
    if user_type is inspect.Signature.empty or '__metadata__' not in dir(user_type):
        return ()
    return [anno for anno in user_type.__metadata__ if isinstance(anno, annotation_type)]  # type: ignore[attr-defined]


MimeType: typing.TypeAlias = str
ResponseCode: typing.TypeAlias = str
MimeMap: typing.TypeAlias = typing.MutableMapping[MimeType, type]
ResponseMap: typing.TypeAlias = typing.Mapping[ResponseCode, MimeMap]


@dc.dataclass
class Responses:
    responses: ResponseMap


class Header(Param, ResponseHandler):
    def __init__(
        self,
        alias: Optional[str] = None,
        /,
        *,
        style: ParamStyle = ParamStyle.simple,
        explode: Optional[bool] = None,
    ) -> None:
        super().__init__(alias, style=style, explode=explode)

    def _apply_request(self, builder: 'RequestBuilder', value: 'ParamValue') -> None:
        builder.headers[self.http_name] = str(value)

    def apply_response(self, response: 'httpx.Response', fields: typing.MutableMapping[str, typing.Any]) -> None:
        # TODO decode
        if self.http_name in response.headers:
            fields[self._name] = response.headers[self.http_name]


class Cookie(Param, ResponseHandler):
    def __init__(
        self,
        alias: Optional[str] = None,
        /,
        *,
        style: ParamStyle = ParamStyle.form,
        explode: Optional[bool] = None,
    ) -> None:
        super().__init__(alias, style=style, explode=explode)

    def _apply_request(self, builder: 'RequestBuilder', value: typing.Any) -> None:
        builder.cookies[self.http_name] = value

    def apply_response(self, response: 'httpx.Response', fields: typing.MutableMapping[str, typing.Any]) -> None:
        # TODO handle decoding
        if self.http_name in response.headers:
            fields[self._name] = response.cookies[self.http_name]


class Path(Param):
    def __init__(
        self,
        alias: Optional[str] = None,
        /,
        *,
        style: ParamStyle = ParamStyle.simple,
        explode: Optional[bool] = None,
    ) -> None:
        super().__init__(alias, style=style, explode=explode)

    def _apply_request(self, builder: 'RequestBuilder', value: typing.Any) -> None:
        builder.path_params[self.http_name] = value


class Query(Param):
    def __init__(
        self,
        alias: Optional[str] = None,
        /,
        *,
        style: ParamStyle = ParamStyle.form,
        explode: Optional[bool] = None,
    ) -> None:
        super().__init__(alias, style=style, explode=explode)

    def _apply_request(self, builder: 'RequestBuilder', value: typing.Any) -> None:
        builder.query_params.append((self.http_name, value))


class Link(NameTypeAwareAnnotation, ResponseHandler):
    def __init__(self, name: str) -> None:
        self._link_name = name

    def apply_response(self, response: httpx.Response, fields: typing.MutableMapping[str, typing.Any]) -> None:
        if 'Link' in response.headers:
            links = response.links
            if self._link_name in links:
                fields[self._name] = links[self._link_name]
