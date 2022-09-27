import inflection

from .modules import RESPONSE_BODY
from .refs import ResolverFunc
from ..module_path import ModulePath
from ..type_ref import resolve_type_ref
from ...openapi import model as openapi


def get_response_map(responses: openapi.Responses, name: str, module: ModulePath, resolve: ResolverFunc) -> dict:
    result = {}
    for resp_code, response in responses.__root__.items():
        if isinstance(response, openapi.Reference):
            response, sub_module, sub_name = resolve(response, openapi.Response)
        else:
            sub_module = module / RESPONSE_BODY
            sub_name = inflection.camelize(name) + resp_code
        if not response.content:
            continue
        mime_map = {}
        for mime, media_type in response.content.items():
            mime_map[mime] = resolve_type_ref(media_type.schema_, sub_module, sub_name, resolve)
        result[resp_code] = mime_map

    return result
