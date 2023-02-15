from dataclasses import dataclass
from typing import Optional

import httpx

from .api_key import ApiKeyAuth
from .. import openapi
from ..model.params import ParamLocation


@dataclass(frozen=True)
class HTTP:
    token: str

    def create(self, model: openapi.HTTPSecurityScheme) -> httpx.Auth:
        return HTTPAuth(model.scheme, self.token, model.bearerFormat)


class HTTPAuth(ApiKeyAuth):
    def __init__(self, scheme: str, token: str, bearer_format: Optional[str] = None):
        value_format_ = bearer_format if bearer_format and scheme.lower() == 'bearer' else '{token}'
        super().__init__(
            api_key=value_format_.format(token=token),
            name='Authorization',
            placement=ParamLocation.header,
        )
