from __future__ import annotations

import abc
from collections.abc import Callable, Mapping, MutableMapping

import httpx
import httpx._transports.base
import httpx_auth
import typing_extensions as typing

from . import _httpx

MultiAuth: typing.TypeAlias = httpx_auth._authentication._MultiAuth  # pylint: disable=protected-access
NamedAuth: typing.TypeAlias = tuple[str, httpx.Auth]
SecurityRequirements: typing.TypeAlias = typing.Mapping[str, typing.Iterable[str]]

MimeType: typing.TypeAlias = str
MimeMap: typing.TypeAlias = MutableMapping[MimeType, type]
Signature: typing.TypeAlias = Mapping[str, typing.Any]
StatusCodeRange: typing.TypeAlias = str
StatusCodeType: typing.TypeAlias = int
SessionFactory: typing.TypeAlias = Callable[..., httpx.AsyncClient]


class Dumper(abc.ABC):
    @abc.abstractmethod
    def __call__(self, obj: typing.Any) -> bytes:
        pass


class Parser(abc.ABC):
    @abc.abstractmethod
    def __call__(self, raw: bytes) -> typing.Any:
        pass


class RequestFactory(typing.Protocol):
    """Protocol for httpx.BaseClient.build_request()"""

    def __call__(  # pylint: disable=too-many-arguments
        self,
        method: str,
        url: str,
        *,
        content: httpx._types.RequestContent | None = None,
        _data: httpx._types.RequestData | None = None,
        _files: httpx._types.RequestFiles | None = None,
        _json: typing.Any | None = None,
        params: httpx._types.QueryParamTypes | None = None,
        headers: httpx._types.HeaderTypes | None = None,
        cookies: httpx._types.CookieTypes | None = None,
        _timeout: httpx._types.TimeoutTypes | _httpx.UseClientDefault = httpx.USE_CLIENT_DEFAULT,
        _extensions: httpx._types.RequestExtensions | None = None,
    ) -> httpx.Request:
        pass


class ClientArgs(typing.TypedDict):
    auth: typing.NotRequired[httpx._types.AuthTypes]
    params: typing.NotRequired[httpx._types.QueryParamTypes]
    headers: typing.NotRequired[httpx._types.HeaderTypes]
    cookies: typing.NotRequired[httpx._types.CookieTypes]
    verify: typing.NotRequired[httpx._types.VerifyTypes]
    cert: typing.NotRequired[httpx._types.CertTypes]
    http1: typing.NotRequired[bool]
    http2: typing.NotRequired[bool]
    proxy: typing.NotRequired[httpx._types.ProxyTypes]
    proxies: typing.NotRequired[httpx._types.ProxiesTypes]
    mounts: typing.NotRequired[typing.Mapping[str, httpx._transports.base.AsyncBaseTransport | None]]
    timeout: typing.NotRequired[httpx._types.TimeoutTypes]
    follow_redirects: typing.NotRequired[bool]
    limits: typing.NotRequired[httpx._config.Limits]
    max_redirects: typing.NotRequired[int]
    event_hooks: typing.NotRequired[typing.Mapping[str, list[typing.Callable[..., typing.Any]]]]
    base_url: typing.NotRequired[httpx._types.URLTypes]
    transport: typing.NotRequired[httpx._transports.base.AsyncBaseTransport]
    app: typing.NotRequired[typing.Callable[..., typing.Any]]
    trust_env: typing.NotRequired[bool]
    default_encoding: typing.NotRequired[str | typing.Callable[[bytes], str]]
