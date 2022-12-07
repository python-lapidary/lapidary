from functools import singledispatch
from typing import Optional, Union, Any, Mapping

from pydantic import BaseModel

from .params import ParamLocation
from ..openapi import model as openapi


class AuthModel(BaseModel):
    pass


class ApiKeyAuthModel(AuthModel):
    param_name: str
    placement: ParamLocation


class HttpAuthModel(AuthModel):
    scheme: str
    bearer_format: Optional[str]


def get_auth_models(model: dict[str, Union[openapi.Reference, openapi.SecurityScheme]]) -> Mapping[str, AuthModel]:
    result: Mapping[str, AuthModel] = {name: get_auth_model(scheme) for name, scheme in model.items()}
    return result


@singledispatch
def get_auth_model(scheme: Any) -> Optional[AuthModel]:
    raise NotImplementedError(scheme)


@get_auth_model.register(openapi.SecurityScheme)
def _(scheme: openapi.SecurityScheme):
    return get_auth_model(scheme.__root__)


@get_auth_model.register(openapi.APIKeySecurityScheme)
def _(scheme: openapi.APIKeySecurityScheme):
    return ApiKeyAuthModel(
        placement=ParamLocation[scheme.in_.value],
        param_name=scheme.name,
    )


@get_auth_model.register(openapi.HTTPSecurityScheme)
def _(scheme: openapi.HTTPSecurityScheme):
    import enum
    scheme_value = scheme.__root__.scheme
    if isinstance(scheme_value, enum.Enum):
        scheme_value = scheme_value.value
    return HttpAuthModel(
        scheme=scheme_value,
        bearer_format=scheme.__root__.bearerFormat,
    )
