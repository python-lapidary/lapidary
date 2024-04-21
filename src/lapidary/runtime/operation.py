import functools as ft
from collections.abc import Iterable
from typing import Optional

import typing_extensions as typing

from .types_ import SecurityRequirements

if typing.TYPE_CHECKING:
    from .client_base import ClientBase


def _operation(
    method: str,
    path: str,
    security: typing.Optional[Iterable[SecurityRequirements]] = None,
) -> typing.Callable:
    def wrapper(fn: typing.Callable):
        @ft.wraps(fn)
        async def operation(self: 'ClientBase', **kwargs) -> typing.Any:
            return await self._request(  # pylint: disable=protected-access
                method,
                path,
                fn,
                security,
                kwargs,
            )

        return operation

    return wrapper


class MethodProto(typing.Protocol):
    def __call__(self, path: str, security: Optional[Iterable[SecurityRequirements]] = None) -> typing.Callable:
        pass


get: MethodProto = ft.partial(_operation, 'GET')
put: MethodProto = ft.partial(_operation, 'PUT')
post: MethodProto = ft.partial(_operation, 'POST')
delete: MethodProto = ft.partial(_operation, 'DELETE')
head: MethodProto = ft.partial(_operation, 'HEAD')
patch: MethodProto = ft.partial(_operation, 'PATCH')
trace: MethodProto = ft.partial(_operation, 'TRACE')
