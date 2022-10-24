from .refs import ResolverFunc
from .response_body import response_type_name
from .type_hint import resolve_type_hint
from ..module_path import ModulePath
from ..names import RESPONSE_BODY
from ...openapi import model as openapi


def get_response_map(responses: openapi.Responses, name: str, module: ModulePath, resolve: ResolverFunc) -> dict:
    result = {}
    for resp_code, response in responses.__root__.items():
        if isinstance(response, openapi.Reference):
            response, sub_module, sub_name = resolve(response, openapi.Response)
        else:
            sub_module = module / RESPONSE_BODY
            sub_name = response_type_name(name, resp_code)
        if not response.content:
            continue
        mime_map = {}
        for mime, media_type in response.content.items():
            mime_map[mime] = resolve_type_hint(media_type.schema_, sub_module, sub_name, resolve)
        result[resp_code] = mime_map

    return result
