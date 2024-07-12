import dataclasses as dc

import pydantic
import typing_extensions as typing

from .http_consts import CONTENT_TYPE, MIME_JSON
from .model.annotations import NameTypeAwareAnnotation, Param
from .model.encode_param import ParamStyle
from .model.request import RequestContributor
from .model.response import ResponseExtractor

if typing.TYPE_CHECKING:
    import httpx

    from ._httpx import ParamValue
    from .model.request import RequestBuilder


@dc.dataclass
class Body(NameTypeAwareAnnotation, RequestContributor):
    content: typing.Mapping[str, type]
    _serializer: typing.Callable[[typing.Any], bytes] = dc.field(init=False)

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


class Header(Param, ResponseExtractor):
    def __init__(
        self,
        alias: typing.Optional[str] = None,
        /,
        *,
        style: ParamStyle = ParamStyle.simple,
        explode: typing.Optional[bool] = None,
    ) -> None:
        super().__init__(alias, style=style, explode=explode)

    def _apply_request(self, builder: 'RequestBuilder', value: 'ParamValue') -> None:
        builder.headers[self.http_name] = str(value)

    def handle_response(self, response: 'httpx.Response') -> typing.Any:
        if self.http_name in response.headers:
            return response.headers[self.http_name]


class Cookie(Param, ResponseExtractor):
    def __init__(
        self,
        alias: typing.Optional[str] = None,
        /,
        *,
        style: ParamStyle = ParamStyle.form,
        explode: typing.Optional[bool] = None,
    ) -> None:
        super().__init__(alias, style=style, explode=explode)

    def _apply_request(self, builder: 'RequestBuilder', value: typing.Any) -> None:
        builder.cookies[self.http_name] = value

    def handle_response(self, response: 'httpx.Response') -> typing.Any:
        if self.http_name in response.headers:
            return response.cookies[self.http_name]


class Path(Param):
    def __init__(
        self,
        alias: typing.Optional[str] = None,
        /,
        *,
        style: ParamStyle = ParamStyle.simple,
        explode: typing.Optional[bool] = None,
    ) -> None:
        super().__init__(alias, style=style, explode=explode)

    def _apply_request(self, builder: 'RequestBuilder', value: typing.Any) -> None:
        builder.path_params[self.http_name] = value


class Query(Param):
    def __init__(
        self,
        alias: typing.Optional[str] = None,
        /,
        *,
        style: ParamStyle = ParamStyle.form,
        explode: typing.Optional[bool] = None,
    ) -> None:
        super().__init__(alias, style=style, explode=explode)

    def _apply_request(self, builder: 'RequestBuilder', value: typing.Any) -> None:
        builder.query_params.append((self.http_name, value))


class Link(NameTypeAwareAnnotation, ResponseExtractor):
    def __init__(self, name: str) -> None:
        self._link_name = name

    def handle_response(self, response: 'httpx.Response') -> typing.Any:
        if 'Link' in response.headers:
            links = response.links
            if self._link_name in links:
                return links[self._link_name]


class StatusCode(ResponseExtractor):
    def handle_response(self, response: 'httpx.Response') -> int:
        return response.status_code
