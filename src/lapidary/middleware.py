from typing import Protocol

import httpx

from .types_ import Next


class HttpxMiddleware(Protocol):
    """
    HTTP middleware protocol, used to fix request or response objects.
    """

    async def __call__(
        self,
        request: httpx.Request,
        next_: Next,
    ) -> httpx.Response:
        """Called for each request. Implementors must call :param:`next_`"""
