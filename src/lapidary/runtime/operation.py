import dataclasses as dc
import functools as ft
from collections.abc import Callable, Iterable

import typing_extensions as typing

from .model.op import mk_exchange_fn, process_operation_method
from .types_ import SecurityRequirements

OperationMethod = typing.TypeVar('OperationMethod', bound=typing.Callable)
SimpleDecorator: typing.TypeAlias = Callable[[OperationMethod], OperationMethod]


@dc.dataclass
class Operation:
    method: str
    path: str
    security: typing.Optional[Iterable[SecurityRequirements]] = None

    def __call__(self, fn: OperationMethod) -> OperationMethod:
        request_adapter, response_handler = process_operation_method(fn, self)
        return typing.cast(OperationMethod, ft.wraps(fn)(mk_exchange_fn(request_adapter, response_handler)))


_operation = Operation


class MethodProto(typing.Protocol):
    def __call__(self, path: str, security: typing.Optional[Iterable[SecurityRequirements]] = None) -> typing.Callable:
        pass


get: MethodProto = ft.partial(_operation, 'GET')
put: MethodProto = ft.partial(_operation, 'PUT')
post: MethodProto = ft.partial(_operation, 'POST')
delete: MethodProto = ft.partial(_operation, 'DELETE')
head: MethodProto = ft.partial(_operation, 'HEAD')
patch: MethodProto = ft.partial(_operation, 'PATCH')
trace: MethodProto = ft.partial(_operation, 'TRACE')
