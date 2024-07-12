import abc
import dataclasses as dc
from collections.abc import Iterable, Mapping
from functools import cache

import httpx
import pydantic
import typing_extensions as typing

from ..http_consts import CONTENT_TYPE
from ..mime import find_mime
from ..types_ import MimeType, ResponseMap
from .annotations import NameTypeAwareAnnotation, find_annotation, find_field_annotation

# base stuff


@cache
def mk_type_adapter(typ: type) -> pydantic.TypeAdapter:
    return pydantic.TypeAdapter(typ)


@dc.dataclass
class Responses:
    responses: ResponseMap


# body handling


# similar structure to openapi responses
ResponseHandlerMap: typing.TypeAlias = Mapping[str, Mapping[MimeType, pydantic.TypeAdapter]]


class ResponseExtractor(abc.ABC):
    @abc.abstractmethod
    def handle_response(self, response: httpx.Response) -> typing.Any:
        pass


@dc.dataclass
class BodyExtractor(ResponseExtractor):
    response_map: Mapping[str, Mapping[str, pydantic.TypeAdapter]]

    def handle_response(self, response: httpx.Response) -> typing.Any:
        typ = self._find_type_adapter(response)
        return typ.validate_json(response.text) if typ else None

    def _find_type_adapter(self, response: httpx.Response) -> typing.Optional[pydantic.TypeAdapter]:
        if not self.response_map:
            return None

        status_code = str(response.status_code)
        if CONTENT_TYPE not in response.headers:
            return None

        media_type = response.headers[CONTENT_TYPE]
        if media_type is None:
            return None

        for code_match in (status_code, status_code[0] + 'XX', 'default'):
            if code_match in self.response_map:
                mime_map = self.response_map[code_match]
                break
        else:
            return None

        mime_match = find_mime(mime_map.keys(), media_type)
        return mime_map[mime_match] if mime_match is not None else None

    @staticmethod
    def for_annotated(annotated: type) -> tuple[ResponseExtractor, Iterable[str]]:
        """return_annotation looks like Annotated[tuple[HeadersModel, Union[ReturnType...]], Responses]
        We need to extract body types from both the return type and the responses.
        Return types present in the response map and not in the return type, should be raise as, or within an exception.
        """
        response_map_anno: Responses
        return_type, response_map_anno = find_annotation(annotated, Responses)

        response_map = {
            status_code: {media_type: mk_type_adapter(typ) for media_type, typ in mime_map.items()}
            for status_code, mime_map in response_map_anno.responses.items()
        }
        media_types = {media_type for mime_map in response_map.values() for media_type in mime_map.keys()}

        return BodyExtractor(response_map), media_types


# header handling


@dc.dataclass
class MetadataExtractor(ResponseExtractor):
    field_extractors: Mapping[str, ResponseExtractor]
    target_type_adapter: pydantic.TypeAdapter

    def handle_response(self, response: httpx.Response) -> typing.Any:
        target_dict = {}
        for field_name, field_extractor in self.field_extractors.items():
            raw_value = field_extractor.handle_response(response)
            if raw_value:
                target_dict[field_name] = raw_value

        return self.target_type_adapter.validate_python(target_dict)

    @staticmethod
    def for_type(metadata_type: type[pydantic.BaseModel]) -> ResponseExtractor:
        header_extractors = {}
        for field_name, field_info in metadata_type.model_fields.items():
            _, extractor = find_field_annotation(field_info, ResponseExtractor)  # type: ignore[type-abstract]
            if isinstance(extractor, NameTypeAwareAnnotation):
                extractor.supply_formal(field_name, field_info.metadata[0])
            header_extractors[field_name] = extractor
        return MetadataExtractor(field_extractors=header_extractors, target_type_adapter=pydantic.TypeAdapter(metadata_type))


# wrap it up


@dc.dataclass
class TupleExtractor(ResponseExtractor):
    response_extractors: Iterable[ResponseExtractor]

    def handle_response(self, response: httpx.Response) -> tuple:
        return tuple(extractor.handle_response(response) for extractor in self.response_extractors)

    @staticmethod
    def for_type(annotated: type) -> tuple[ResponseExtractor, Iterable[str]]:
        return_type, responses = find_annotation(annotated, Responses)
        body_type, meta_type = typing.get_args(return_type)
        body_extractor, media_types = BodyExtractor.for_annotated(annotated)
        return TupleExtractor(
            response_extractors=(
                body_extractor,
                MetadataExtractor.for_type(meta_type),
            )
        ), media_types


def mk_response_extractor(annotated: type) -> tuple[ResponseExtractor, Iterable[str]]:
    if typing.get_origin(typing.get_args(annotated)[0]) is tuple:
        return TupleExtractor.for_type(annotated)
    else:
        return BodyExtractor.for_annotated(annotated)
