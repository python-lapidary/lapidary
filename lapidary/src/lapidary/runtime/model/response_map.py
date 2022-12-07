from typing import Union, Type, TypeVar, Mapping

from .refs import ResolverFunc, get_resolver
from .type_hint import resolve_type_hint
from ..module_path import ModulePath
from ..names import RESPONSE_BODY, response_type_name
from ..openapi import model as openapi
from ..types import resolve

T = TypeVar('T')
MimeMap = Mapping[str, Type[T]]
ResponseMap = Mapping[str, MimeMap]


def get_response_map(
        responses: openapi.Responses, op_name: str, module: ModulePath, resolve_ref: ResolverFunc
) -> ResponseMap:
    result = {}
    for resp_code, response in responses.__root__.items():
        response, sub_module, sub_name = resolve_response(resp_code, response, op_name, module, resolve_ref)
        if not response.content:
            continue

        mime_map = {}
        for mime, media_type in response.content.items():
            mime_map[mime] = resolve_type_hint(media_type.schema_, sub_module, sub_name, resolve_ref).resolve()

        result[resp_code] = mime_map

    return result


def resolve_response(
        resp_code: str,
        response: Union[openapi.Response, openapi.Reference],
        op_name: str,
        module: ModulePath,
        resolve_ref: ResolverFunc
) -> tuple[openapi.Response, ModulePath, str]:
    if isinstance(response, openapi.Reference):
        response, sub_module, sub_name = resolve_ref(response, openapi.Response)
    else:
        sub_module = module / RESPONSE_BODY
        response_type_name(op_name, resp_code)
        sub_name = response_type_name(op_name, resp_code)
    return response, sub_module, sub_name


def get_api_responses(model: openapi.OpenApiModel, module: ModulePath) -> ResponseMap:
    resolve_ref = get_resolver(model, module.str())

    result = {}
    for status, media_map in model.lapidary_responses_global.__root__.items():
        if isinstance(media_map, openapi.Reference):
            media_map, module, name = resolve_ref(media_map, openapi.Response)
        if media_map.content is not None:
            result[status] = {
                media_type_name: resolve_type(media_type.schema_, module, resolve_ref) for media_type_name, media_type in media_map.content.items() if
                media_type.schema_ is not None
            }
    return result


def resolve_type(schema: Union[openapi.Schema, openapi.Reference], module: ModulePath, resolve_ref: ResolverFunc) -> Type:
    if isinstance(schema, openapi.Reference):
        _, module, name = resolve_ref(schema, openapi.Schema)
    elif schema.lapidary_name is not None:
        name = schema.lapidary_name
    else:
        raise NotImplementedError('Schema needs name')
    return resolve(module.str(), name)
