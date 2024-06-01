import functools as ft
from collections.abc import Iterable
from typing import Optional

import typing_extensions as typing

from .model.op import OperationModel
from .types_ import SecurityRequirements

if typing.TYPE_CHECKING:
    from .client_base import ClientBase


def _operation(
    method: str,
    path: str,
    security: typing.Optional[Iterable[SecurityRequirements]] = None,
) -> typing.Callable:
    def decorator(fn: typing.Callable):
        op = OperationModel(
            method,
            path,
            security,
            fn,
        )

        @ft.wraps(fn)
        def capture(self: 'ClientBase', **kwargs):
            return op(self, **kwargs)

        return capture

    return decorator


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
