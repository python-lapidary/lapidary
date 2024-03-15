__all__ = [
    'APIKeyAuth',
    'AuthType',
    'MultiAuth',
    'NamedAuth',
    'SecurityRequirements',
]

import abc
import dataclasses as dc

import httpx
import httpx_auth
import typing_extensions as typing

from . import _httpx
from .model.api_key import CookieApiKey

AuthType: typing.TypeAlias = typing.Union[httpx.Auth, _httpx.UseClientDefault, None]
MultiAuth: typing.TypeAlias = httpx_auth._authentication._MultiAuth  # pylint: disable=protected-access
NamedAuth: typing.TypeAlias = tuple[str, httpx.Auth]
SecurityRequirements: typing.TypeAlias = typing.Mapping[str, typing.Iterable[str]]


@dc.dataclass
class AuthFactory(abc.ABC):
    security_name: str

    @abc.abstractmethod
    def __call__(self, body: object) -> NamedAuth:
        pass


APIKeyAuthLocation: typing.TypeAlias = typing.Literal['cookie', 'header', 'query']

api_key_in: typing.Mapping[APIKeyAuthLocation, type[httpx.Auth]] = {
    'cookie': CookieApiKey,
    'header': httpx_auth.authentication.HeaderApiKey,
    'query': httpx_auth.authentication.QueryApiKey,
}


@dc.dataclass
class APIKeyAuth(AuthFactory):
    in_: APIKeyAuthLocation
    name: str
    format: str

    def __call__(self, body: object) -> NamedAuth:
        typ = api_key_in[self.in_]
        return self.security_name, typ(self.format.format(body=body), self.name)  # type: ignore[misc]
