import dataclasses as dc
import functools as ft
from collections.abc import Callable

import typing_extensions as typing

from .model.op import mk_exchange_fn

OperationMethod = typing.TypeVar('OperationMethod', bound=typing.Callable)
SimpleDecorator: typing.TypeAlias = Callable[[OperationMethod], OperationMethod]


@dc.dataclass
class Operation:
    method: str
    path: str
    security: None = None  # deprecated, not used, TODO remove

    def __call__(self, fn: OperationMethod) -> OperationMethod:
        exchange_fn = mk_exchange_fn(fn, self)
        return typing.cast(OperationMethod, ft.wraps(fn)(exchange_fn))


class MethodProto(typing.Protocol):
    def __call__(self, path: str) -> typing.Callable:
        pass


get: MethodProto = ft.partial(Operation, 'GET')
put: MethodProto = ft.partial(Operation, 'PUT')
post: MethodProto = ft.partial(Operation, 'POST')
delete: MethodProto = ft.partial(Operation, 'DELETE')
head: MethodProto = ft.partial(Operation, 'HEAD')
patch: MethodProto = ft.partial(Operation, 'PATCH')
trace: MethodProto = ft.partial(Operation, 'TRACE')
