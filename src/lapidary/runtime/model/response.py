import abc
import dataclasses as dc
from collections.abc import Callable, Iterable, Mapping
from typing import Optional

import httpx
import pydantic
import typing_extensions as typing

from ..annotations import Cookie, Header, Link, Param, Responses, StatusCode, WebArg
from ..http_consts import CONTENT_TYPE
from ..metattype import is_array_like, make_not_optional
from ..mime import find_mime
from ..type_adapter import TypeAdapter, mk_type_adapter
from ..types_ import MimeType, StatusCodeRange, StatusCodeType
from .annotations import find_annotation, find_field_annotation
from .error import UnexpectedResponse
from .param_serialization import SCALAR_TYPES, ValueType


class ResponseExtractor(abc.ABC):
    @abc.abstractmethod
    def handle_response(self, response: 'httpx.Response') -> typing.Any:
        pass


class NoopExtractor(ResponseExtractor):
    def handle_response(self, response: 'httpx.Response') -> None:
        return None


_NOOP = NoopExtractor()


@dc.dataclass
class BodyExtractor(ResponseExtractor):
    type_adapter: typing.Optional[TypeAdapter]

    def handle_response(self, response: httpx.Response) -> typing.Any:
        try:
            return self.type_adapter(response.text) if self.type_adapter else None
        except pydantic.ValidationError as e:
            raise UnexpectedResponse(response) from e


# header handling


@dc.dataclass
class ParamExtractor(ResponseExtractor, abc.ABC):
    param: Param
    python_name: str
    python_type: type
    _deserializer: Callable[[str], ValueType] = dc.field(init=False)

    def __post_init__(self):
        non_optional_type = make_not_optional(self.python_type)
        if non_optional_type in SCALAR_TYPES:
            self._deserialize = self.param.style.deserialize_scalar
        elif is_array_like(non_optional_type):
            self._deserialize = self.param.style.deserialize_array
        else:
            self._deserialize = self.param.style.deserialize

    def handle_response(self, response: 'httpx.Response') -> typing.Any:
        part = self._get_response_part(response)
        value = part[self.http_name()]
        if value is None:
            return None
        return self._deserialize(value, make_not_optional(self.python_type))

    @staticmethod
    @abc.abstractmethod
    def _get_response_part(response: 'httpx.Response') -> Mapping[str, str]:
        pass

    def http_name(self) -> str:
        return self.param.alias or self.python_name


class HeaderExtractor(ParamExtractor):
    @staticmethod
    def _get_response_part(response: 'httpx.Response') -> Mapping[str, str]:
        return response.headers


class CookieExtractor(ParamExtractor):
    @staticmethod
    def _get_response_part(response: 'httpx.Response') -> Mapping[str, str]:
        return response.cookies


class LinkExtractor(ParamExtractor):
    @staticmethod
    def _get_response_part(response: 'httpx.Response') -> Mapping[str, str]:
        if 'lapidary_links' not in dir(response):
            links = {}
            for link in response.links.values():
                try:
                    links[link['rel']] = link['url']
                except KeyError:
                    continue
            response.links_cached = links
        return response.lapidary_links


class StatusCodeExtractor(ResponseExtractor):
    def __init__(self, _webarg: WebArg, _field_name: str, _typ: typing.Any) -> None:
        pass

    def handle_response(self, response: 'httpx.Response') -> int:
        return response.status_code


EXTRACTOR_MAP = {
    Header: HeaderExtractor,
    Cookie: CookieExtractor,
    Link: LinkExtractor,
    StatusCode: StatusCodeExtractor,
}


@dc.dataclass
class MetadataExtractor(ResponseExtractor):
    field_extractors: Mapping[str, ResponseExtractor]
    target_type_adapter: TypeAdapter

    def handle_response(self, response: httpx.Response) -> typing.Any:
        target_dict = {}
        for field_name, field_extractor in self.field_extractors.items():
            try:
                raw_value = field_extractor.handle_response(response)
                target_dict[field_name] = raw_value
            except KeyError:
                continue

        return self.target_type_adapter(target_dict)

    @staticmethod
    def for_type(metadata_type: type[pydantic.BaseModel]) -> ResponseExtractor:
        header_extractors = {}
        for field_name, field_info in metadata_type.model_fields.items():
            try:
                typ, webarg = find_field_annotation(field_info, WebArg)
            except TypeError:
                raise TypeError('Problem with annotations', field_name)
            try:
                extractor = EXTRACTOR_MAP[type(webarg)](webarg, field_name, typ)  # type: ignore[abstract, arg-type]
            except KeyError:
                raise TypeError('Unsupported annotation', field_name, webarg)
            header_extractors[field_name] = extractor
        return MetadataExtractor(field_extractors=header_extractors, target_type_adapter=mk_type_adapter(metadata_type, json=False))


# wrap it up


@dc.dataclass
class TupleExtractor(ResponseExtractor):
    response_extractors: Iterable[ResponseExtractor]

    def handle_response(self, response: httpx.Response) -> tuple:
        return tuple(extractor.handle_response(response) for extractor in self.response_extractors)


_NOOP_TUPLE = TupleExtractor(response_extractors=(_NOOP, _NOOP))


# similar structure to openapi responses
ResponseExtractorMap: typing.TypeAlias = dict[StatusCodeRange, dict[Optional[MimeType], ResponseExtractor]]


@dc.dataclass
class ResponseMessageExtractor(ResponseExtractor):
    response_map: ResponseExtractorMap

    def handle_response(self, response: 'httpx.Response') -> tuple[StatusCodeType, tuple[typing.Any, typing.Any]]:
        extractor = self._find_extractor(response)
        return response.status_code, extractor.handle_response(response)

    def _find_extractor(self, response: httpx.Response) -> ResponseExtractor:
        if not self.response_map:
            raise UnexpectedResponse(response)

        status_code = str(response.status_code)
        for code_match in (status_code, status_code[0] + 'XX', 'default'):
            try:
                mime_map = self.response_map[code_match]
                break
            except KeyError:
                pass
        else:
            raise UnexpectedResponse(response)

        try:
            media_type = response.headers[CONTENT_TYPE]
        except KeyError:
            return _NOOP_TUPLE

        mime_match = find_mime([media_type_ for media_type_ in mime_map.keys() if media_type_ is not None], media_type)
        if not mime_match:
            raise UnexpectedResponse(response)
        return mime_map[mime_match]

    @staticmethod
    def for_annotated(responses: Responses) -> 'tuple[ResponseMessageExtractor, Iterable[str]]':
        # Ideally Lapidary should avoid the first Annotated argument (the type) and leave it to type checkers.
        # Instead it should focus on the `Responses` annotation.

        response_map: ResponseExtractorMap = {}
        media_types = set()
        for status_code, response in responses.responses.items():
            response_map[status_code] = {}
            headers_extractor = MetadataExtractor.for_type(response.headers) if response.headers else _NOOP
            for media_type, typ in response.body.content.items():
                response_map[status_code][media_type] = TupleExtractor(
                    (
                        BodyExtractor(mk_type_adapter(typ, json=True)),
                        headers_extractor,
                    )
                )
                media_types.add(media_type)
            else:
                response_map[status_code][None] = TupleExtractor(
                    (
                        _NOOP,
                        headers_extractor,
                    )
                )

        return ResponseMessageExtractor(response_map), media_types


def mk_response_extractor(annotated: type) -> tuple[ResponseMessageExtractor, Iterable[MimeType]]:
    _, responses = find_annotation(annotated, Responses)
    return ResponseMessageExtractor.for_annotated(responses)
