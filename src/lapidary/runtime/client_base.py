from __future__ import annotations

import abc
import logging
from collections.abc import Sequence

import httpx
import typing_extensions as typing

from .middleware import HttpxMiddleware
from .model.op import mk_send as _mk_send

logger = logging.getLogger(__name__)


class ClientBase(abc.ABC):
    """Base for Client classes"""

    def __init__(
        self,
        client: httpx.AsyncClient | None = None,
        base_url: str | None = None,
        *,
        middlewares: Sequence[HttpxMiddleware] = (),
        auth: httpx.Auth | None = None,
    ) -> None:
        """
        :param client: the httpx client to use
        :param middlewares: list of middlewares to process HTTP requests and responses
        """
        self._base_url = base_url
        self._client = client or httpx.AsyncClient()
        self._auth = auth
        self._middlewares = middlewares
        self._send = _mk_send(self._client.send, self._auth, self._middlewares)


T = typing.TypeVar('T', bound=ClientBase)


def with_auth(original: T, auth: httpx.Auth | None) -> T:
    import copy

    copied = copy.copy(original)
    copied._auth = auth
    copied._send = _mk_send(copied._client.send, copied._auth, copied._middlewares)
    return copied
