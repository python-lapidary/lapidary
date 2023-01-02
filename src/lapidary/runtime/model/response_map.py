import pkgutil
from collections.abc import Mapping
from typing import Union, TypeVar, NamedTuple

from .refs import ResolverFunc, get_resolver
from .type_hint import get_type_hint
from .. import openapi
from ..module_path import ModulePath
from ..names import RESPONSE_BODY, response_type_name
from ..openapi import model as openapi, LapidaryModelType

T = TypeVar('T')
MimeType = ResponseCode = str


class ReturnTypeInfo(NamedTuple):
    type_: type
    iterator: bool = False


MimeMap = Mapping[MimeType, ReturnTypeInfo]
ResponseMap = Mapping[ResponseCode, MimeMap]


def get_response_map(
        responses: openapi.Responses, op_name: str, module: ModulePath, resolve_ref: ResolverFunc
) -> ResponseMap:
    result = {}
    for resp_code, response in responses.items():
        response, sub_module, sub_name = resolve_response(resp_code, response, op_name, module, resolve_ref)
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
            mime_map[mime] = ReturnTypeInfo(type_, resp_schema.lapidary_model_type is LapidaryModelType.iterator)

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
    return get_response_map(model.lapidary_responses_global, 'API', module, resolve_ref)


def resolve_type(schema: Union[openapi.Schema, openapi.Reference], module: ModulePath, resolve_ref: ResolverFunc) -> type:
    if isinstance(schema, openapi.Reference):
        _, module, name = resolve_ref(schema, openapi.Schema)
    elif schema.lapidary_name is not None:
        name = schema.lapidary_name
    else:
        raise NotImplementedError('Schema needs name')
    return pkgutil.resolve_name(module.str() + ':' + name)
