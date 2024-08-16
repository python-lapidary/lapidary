from __future__ import annotations

import abc
import logging
from importlib.metadata import version

import httpx
import typing_extensions as typing

from .model.auth import AuthRegistry

if typing.TYPE_CHECKING:
    import types
    from collections.abc import Iterable

    from .types_ import NamedAuth, SecurityRequirements

logger = logging.getLogger(__name__)

USER_AGENT = f'lapidary.dev/{version("lapidary")}'


class ClientBase(abc.ABC):
    def __init__(
        self,
        base_url: str,
        user_agent: str = USER_AGENT,
        security: Iterable[SecurityRequirements] | None = None,
        _http_client: httpx.AsyncClient | None = None,
        **httpx_kwargs,
    ):
        if httpx_kwargs and _http_client:
            raise TypeError(f'Extra keyword arguments not accepted when passing _http_client: {", ".join(httpx_kwargs.keys())}')

        headers = httpx.Headers(httpx_kwargs.pop('headers', None))
        if user_agent:
            headers['User-Agent'] = user_agent

        self._client = _http_client or httpx.AsyncClient(base_url=base_url, headers=headers, **httpx_kwargs)
        self._auth_registry = AuthRegistry(security)

    async def __aenter__(self: typing.Self) -> typing.Self:
        await self._client.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_value: BaseException | None = None,
        traceback: types.TracebackType | None = None,
    ) -> bool | None:
        return await self._client.__aexit__(exc_type, exc_value, traceback)

    def lapidary_authenticate(self, *auth_args: NamedAuth, **auth_kwargs: httpx.Auth) -> None:
        """Register named Auth instances for future use with methods that require authentication."""
        if auth_args:
            # make python complain about duplicate names
            self.lapidary_authenticate(**dict(auth_args), **auth_kwargs)

        self._auth_registry.authenticate(auth_kwargs)

    def lapidary_deauthenticate(self, *sec_names: str) -> None:
        """Remove reference to a given Auth instance.
        Calling with no parameters removes all references"""

        self._auth_registry.deauthenticate(sec_names)
