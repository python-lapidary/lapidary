from collections.abc import Collection, Mapping
from functools import singledispatch
from typing import Any, Optional, Union

from lapidary_base import ParamPlacement
from pydantic import BaseModel, Field

from .client_func_response_map import get_response_map
from .refs import ResolverFunc
from .type_hint import TypeHint, BuiltinTypeHint
from ..module_path import ModulePath
from ...openapi import model as openapi


class AuthModel(BaseModel):
    auth_name: str


class ApiKeyAuthModel(AuthModel):
    key: str
    param_name: str
    placement: ParamPlacement


class HttpAuthModel(AuthModel):
    scheme: str
    bearer_format: Optional[str]
    param_name: str


class ClientInit(BaseModel):
    auth_models: list[AuthModel] = Field(default_factory=list)
    base_urls: list[str] = Field(default_factory=list)
    headers: list[tuple[str, str]] = Field(default_factory=list)
    init_auth_params: dict[str, TypeHint] = Field(default_factory=dict)
    response_map: dict[str, dict[str, TypeHint]] = Field(default_factory=dict)
    default_auth: Optional[str]


def get_client_init(openapi_model: openapi.OpenApiModel, module: ModulePath, resolve: ResolverFunc) -> ClientInit:
    if openapi_model.components and openapi_model.components.securitySchemes:
        auth_models = get_auth_models(openapi_model.components.securitySchemes)
        auth_params = get_init_auth_params(openapi_model.components.securitySchemes)
    else:
        auth_models = []
        auth_params = {}

    response_map = get_response_map(
        openapi_model.lapidary_responses_global,
        'LapidaryGlobalResponses',
        module,
        resolve
    ) if openapi_model.lapidary_responses_global else {}

    default_auth = next(iter(openapi_model.security[0].__root__.keys())) if openapi_model.security else None

    return ClientInit(
        auth_models=auth_models,
        init_auth_params=auth_params,
        base_urls=[server.url for server in openapi_model.servers] if openapi_model.servers else [],
        headers=get_global_headers(openapi_model.lapidary_headers_global),
        response_map=response_map,
        default_auth=default_auth,
    )


def get_global_headers(global_headers: Optional[Union[
    dict[str, Union[str, list[str]]],
    list[tuple[str, str]]
]]) -> list[tuple[str, str]]:
    if global_headers is None:
        return []

    result_headers = []
    input_header_list = global_headers.items() if isinstance(global_headers, Mapping) else global_headers
    for key, values in input_header_list:
        if not isinstance(values, Collection) or isinstance(values, str):
            values = [values]
        for value in values:
            result_headers.append((key, value,))

    return result_headers


def get_auth_models(model: dict[str, Union[openapi.Reference, openapi.SecurityScheme]]) -> list[AuthModel]:
    result: list[AuthModel] = [get_auth_model(scheme, name) for name, scheme in model.items()]
    return [m for m in result if m is not None]


@singledispatch
def get_auth_model(_scheme: Any, _name: str) -> Optional[AuthModel]:
    # ignore
    pass


@get_auth_model.register(openapi.SecurityScheme)
def _(scheme: openapi.SecurityScheme, name: str):
    return get_auth_model(scheme.__root__, name)


@get_auth_model.register(openapi.APIKeySecurityScheme)
def _(scheme: openapi.APIKeySecurityScheme, name: str):
    return ApiKeyAuthModel(
        auth_name=name,
        key=scheme.name,
        placement=ParamPlacement[scheme.in_.value],
        param_name=name + '_' + scheme.name.lower(),
    )


@get_auth_model.register(openapi.HTTPSecurityScheme)
def _(scheme: openapi.HTTPSecurityScheme, name: str):
    import enum
    scheme_value = scheme.__root__.scheme
    if isinstance(scheme_value, enum.Enum):
        scheme_value = scheme_value.value
    return HttpAuthModel(
        auth_name=name,
        scheme=scheme_value,
        bearer_format=scheme.__root__.bearerFormat,
        param_name=name + '_token'
    )


def get_init_auth_params(schemes: dict[str, openapi.SecurityScheme]) -> dict[str, TypeHint]:
    params: dict[str, TypeHint] = {}
    for scheme_name, scheme in schemes.items():
        if isinstance(scheme, openapi.Reference):
            raise NotImplementedError(type(scheme))
        params[get_auth_params(scheme.__root__, scheme_name)] = BuiltinTypeHint.from_str('str')

    return params


@singledispatch
def get_auth_params(scheme: Any, _name: str):
    raise NotImplementedError(type(scheme))


@get_auth_params.register(openapi.APIKeySecurityScheme)
def _(scheme: openapi.APIKeySecurityScheme, name: str) -> str:
    return f'{name}_{scheme.name.lower()}'


@get_auth_params.register(openapi.HTTPSecurityScheme)
def _(_, name: str) -> str:
    return f'{name}_token'
