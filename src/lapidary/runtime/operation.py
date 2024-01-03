import functools as ft
from typing import Callable
import typing as ty

from .model.op import LapidaryOperation, Operation

if ty.TYPE_CHECKING:
    from .client_base import ClientBase


def _operation(
        method: str,
        path: str,
) -> Callable:
    def wrapper(fn: Callable):
        fn.lapidary_operation = Operation(method, path)
        fn.lapidary_operation_model = None

        @ft.wraps(fn)
        async def operation(self: 'ClientBase', **kwargs) -> ty.Any:
            return await self._request(
                ty.cast(LapidaryOperation, fn),
                kwargs,
            )

        return operation

    return wrapper


GET = ft.partial(_operation, 'GET')
PUT = ft.partial(_operation, 'PUT')
POST = ft.partial(_operation, 'POST')
DELETE = ft.partial(_operation, 'DELETE')
HEAD = ft.partial(_operation, 'HEAD')
PATCH = ft.partial(_operation, 'PATCH')
TRACE = ft.partial(_operation, 'TRACE')
