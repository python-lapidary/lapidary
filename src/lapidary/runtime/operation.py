import functools as ft

from .compat import typing as ty
from .model.op import LapidaryOperation, Operation

if ty.TYPE_CHECKING:
    from .client_base import ClientBase


def _operation(
        method: str,
        path: str,
) -> ty.Callable:
    def wrapper(fn: ty.Callable):
        fn_ = ty.cast(LapidaryOperation, fn)
        fn_.lapidary_operation = Operation(method, path)
        fn_.lapidary_operation_model = None

        @ft.wraps(fn)
        async def operation(self: 'ClientBase', **kwargs) -> ty.Any:
            return await self._request(  # pylint: disable=protected-access
                ty.cast(LapidaryOperation, fn),
                kwargs,
            )

        return operation

    return wrapper


class MethodProto(ty.Protocol):
    def __call__(self, path: str) -> ty.Callable:
        pass


GET: MethodProto = ft.partial(_operation, 'GET')
PUT: MethodProto = ft.partial(_operation, 'PUT')
POST: MethodProto = ft.partial(_operation, 'POST')
DELETE: MethodProto = ft.partial(_operation, 'DELETE')
HEAD: MethodProto = ft.partial(_operation, 'HEAD')
PATCH: MethodProto = ft.partial(_operation, 'PATCH')
TRACE: MethodProto = ft.partial(_operation, 'TRACE')
