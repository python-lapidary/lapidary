import functools as ft
import inspect
from collections.abc import Iterable
from typing import Optional

import typing_extensions as typing

from .model.annotations import ResponseMap, Responses, find_annotations
from .model.op import DefaultEnvelope, OperationModel
from .model.response import ResponseEnvelope
from .request import process_params
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


def get_response_map(return_anno: type) -> ResponseMap:
    annos: typing.Sequence[Responses] = find_annotations(return_anno, Responses)
    if len(annos) != 1:
        raise TypeError('Operation function must have exactly one Responses annotation')

    responses = annos[0].responses
    for media_type_map in responses.values():
        for media_type, typ in media_type_map.items():
            if not issubclass(typ, ResponseEnvelope):
                media_type_map[media_type] = DefaultEnvelope[typ]  # type: ignore[valid-type]
    return responses


def get_operation_model(
    method: str,
    path: str,
    fn: typing.Callable,
) -> OperationModel:
    sig = inspect.signature(fn)
    return OperationModel(
        method=method,
        path=path,
        params=process_params(sig),
        response_map=get_response_map(sig.return_annotation),
    )
