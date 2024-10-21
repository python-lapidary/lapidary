from __future__ import annotations

import abc
import logging

import httpx
import typing_extensions as typing

from .http_consts import USER_AGENT
from .middleware import HttpxMiddleware
from .model.auth import AuthRegistry

if typing.TYPE_CHECKING:
    import types
    from collections.abc import Iterable, Sequence

    from .types_ import ClientArgs, NamedAuth, SecurityRequirements, SessionFactory

logger = logging.getLogger(__name__)


def lapidary_user_agent() -> str:
    from importlib.metadata import version

    return f'Lapidary/{version("lapidary")}'


class ClientBase(abc.ABC):
    def __init__(
        self,
        security: Iterable[SecurityRequirements] | None = None,
        session_factory: SessionFactory = httpx.AsyncClient,
        middlewares: Sequence[HttpxMiddleware] = (),
        **httpx_kwargs: typing.Unpack[ClientArgs],
    ) -> None:
        self._client = session_factory(**httpx_kwargs)
        if USER_AGENT not in self._client.headers:
            self._client.headers[USER_AGENT] = lapidary_user_agent()

        self._auth_registry = AuthRegistry(security)
        self._middlewares = middlewares

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
