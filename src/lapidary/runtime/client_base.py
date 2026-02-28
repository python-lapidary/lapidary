from __future__ import annotations

import abc
import logging

import httpx
import typing_extensions as typing

from .middleware import HttpxMiddleware
from .model.auth import AuthRegistry

if typing.TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from .types_ import NamedAuth, SecurityRequirements

logger = logging.getLogger(__name__)


def lapidary_user_agent() -> str:
    from importlib.metadata import version

    return f'Lapidary/{version("lapidary")}'


class ClientBase(abc.ABC):
    """Base for Client classes"""

    def __init__(
        self,
        security: Iterable[SecurityRequirements] | None = None,
        client: httpx.AsyncClient | None = None,
        base_url: str | None = None,
        middlewares: Sequence[HttpxMiddleware] = (),
    ) -> None:
        """
        :param security: Security requirements as a mapping of name => list of scopes
        :param client: the httpx client to use
        :param middlewares: list of middlewares to process HTTP requests and responses
        """
        self._base_url = base_url
        self._client = client or httpx.AsyncClient()
        self._auth_registry = AuthRegistry(security)
        self._middlewares = middlewares

    def lapidary_authenticate(self, *auth_args: NamedAuth, **auth_kwargs: httpx.Auth) -> None:
        """
        Register named Auth instances for future use with methods that require authentication.
        Accepts named [`Auth`][httpx.Auth] as tuples name, auth or as named arguments
        """
        if auth_args:
            # make python complain about duplicate names
            self.lapidary_authenticate(**dict(auth_args), **auth_kwargs)
        else:
            self._auth_registry.authenticate(auth_kwargs)

    def lapidary_deauthenticate(self, *sec_names: str) -> None:
        """Remove reference to a given Auth instance.
        Calling with no parameters removes all references"""

        self._auth_registry.deauthenticate(sec_names)
