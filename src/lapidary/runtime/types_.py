from __future__ import annotations

import abc
from collections.abc import Awaitable, Callable, Mapping, MutableMapping

import httpx
import typing_extensions as typing

from . import _httpx

MimeType: typing.TypeAlias = str
MimeMap: typing.TypeAlias = MutableMapping[MimeType, type]
Signature: typing.TypeAlias = Mapping[str, typing.Any]
StatusCodeRange: typing.TypeAlias = str
StatusCodeType: typing.TypeAlias = int

Next: typing.TypeAlias = Callable[[httpx.Request], Awaitable[httpx.Response]]


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
