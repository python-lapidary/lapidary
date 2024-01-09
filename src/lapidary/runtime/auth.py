__all__ = [
    'APIKeyAuth',
    'MultiAuth',
]

import abc
import dataclasses as dc
from typing import Mapping
import typing as ty

import httpx
import httpx_auth
from httpx_auth.authentication import _MultiAuth as MultiAuth, _MultiAuth

from .compat import typing as ty
from .model.api_key import CookieApiKey

AuthType = ty.TypeVar("AuthType", bound=httpx.Auth)


class AuthFactory(abc.ABC):
    @abc.abstractmethod
    def __call__(self, body: object) -> httpx.Auth:
        pass


APIKeyAuthLocation: ty.TypeAlias = ty.Literal['cookie', 'header', 'query']

api_key_in: ty.Mapping[APIKeyAuthLocation, ty.Type[AuthType]] = {
    'cookie': CookieApiKey,
    'header': httpx_auth.authentication.HeaderApiKey,
    'query': httpx_auth.authentication.QueryApiKey,
}


@dc.dataclass
class APIKeyAuth(AuthFactory):
    in_: APIKeyAuthLocation
    name: str
    format: str

    def __call__(self, body: object) -> httpx.Auth:
        typ = api_key_in[self.in_]
        return typ(self.format.format(body=body), self.name)


def get_auth(params: Mapping[str, ty.Any]) -> ty.Optional[httpx.Auth]:
    auth_params = [value for value in params.values() if isinstance(value, httpx.Auth)]
    auth_num = len(auth_params)
    if auth_num == 0:
        return None
    elif auth_num == 1:
        return auth_params[0]
    else:
        return MultiAuth(*auth_params)
