from typing import Union, TypeVar, NamedTuple, Tuple, Mapping

from .refs import ResolverFunc, get_resolver
from .types import get_type_hint
from .. import openapi
from ..json_pointer import encode_json_pointer
from ..module_path import ModulePath

T = TypeVar('T')
MimeType = str
ResponseCode = str


class ReturnTypeInfo(NamedTuple):
    type_: type
    iterator: bool = False


MimeMap = Mapping[MimeType, ReturnTypeInfo]
ResponseMap = Mapping[ResponseCode, MimeMap]


def get_response_map(
        responses: openapi.Responses, module: ModulePath, resolve_ref: ResolverFunc
) -> ResponseMap:
    result = {}
    for resp_code, response in responses.items():
        response, sub_module, sub_name = resolve_response(resp_code, response, module, resolve_ref)
        if not response.content:
            continue

        mime_map = {}
        for mime, media_type in response.content.items():
            if isinstance(media_type.schema_, openapi.Reference):
                resp_schema, resp_module, resp_name = resolve_ref(media_type.schema_, openapi.Schema)
            else:
                resp_schema = media_type.schema_
                resp_module = sub_module
                resp_name = sub_name
            type_ = get_type_hint(resp_schema, resp_module, resp_name, True, resolve_ref).resolve()
            mime_map[mime] = ReturnTypeInfo(type_, resp_schema.lapidary_model_type is openapi.LapidaryModelType.ITERATOR)

        result[resp_code] = mime_map

    return result


def resolve_response(
        resp_code: str,
        response: Union[openapi.Response, openapi.Reference],
        module: ModulePath,
        resolve_ref: ResolverFunc
) -> Tuple[openapi.Response, ModulePath, str]:
    if isinstance(response, openapi.Reference):
        response_, sub_module, sub_name = resolve_ref(response, openapi.Response)
    else:
        response_ = response
        sub_module = module / encode_json_pointer(resp_code) / "content"
        sub_name = "schema"
    return response_, sub_module, sub_name


def get_api_responses(model: openapi.OpenApiModel, module: ModulePath) -> ResponseMap:
    resolve_ref = get_resolver(model, str(module))
    return get_response_map(model.lapidary_responses_global, module, resolve_ref)
