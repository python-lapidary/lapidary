from dataclasses import dataclass
from typing import Optional

import httpx

from .api_key import ApiKeyAuth
from ..model.auth import HttpAuthModel
from ..model.params import ParamLocation


@dataclass(frozen=True)
class HTTP:
    token: str

    def create(self, model: HttpAuthModel) -> httpx.Auth:
        return HTTPAuth(model.scheme, self.token, model.bearer_format)


class HTTPAuth(ApiKeyAuth):
    def __init__(self, scheme: str, token: str, bearer_format: Optional[str] = None):
        value_format = 'Bearer {token}' if scheme.lower() == 'bearer' else bearer_format
        super().__init__(
            api_key=value_format.format(token=token),
            name='Authorization',
            placement=ParamLocation.header,
        )
