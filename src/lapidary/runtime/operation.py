import functools as ft

from .compat import typing as ty

if ty.TYPE_CHECKING:
    from .client_base import ClientBase


def _operation(
        method: str,
        path: str,
) -> ty.Callable:
    def wrapper(fn: ty.Callable):
        @ft.wraps(fn)
        async def operation(self: 'ClientBase', **kwargs) -> ty.Any:
            return await self._request(  # pylint: disable=protected-access
                method,
                path,
                fn,
                kwargs,
            )

        return operation

    return wrapper


class MethodProto(ty.Protocol):
    def __call__(self, path: str) -> ty.Callable:
        pass


get: MethodProto = ft.partial(_operation, 'GET')
put: MethodProto = ft.partial(_operation, 'PUT')
post: MethodProto = ft.partial(_operation, 'POST')
delete: MethodProto = ft.partial(_operation, 'DELETE')
head: MethodProto = ft.partial(_operation, 'HEAD')
patch: MethodProto = ft.partial(_operation, 'PATCH')
trace: MethodProto = ft.partial(_operation, 'TRACE')
