import inspect
from collections.abc import Awaitable, Iterable
from typing import Callable

import typing_extensions as typing

from .annotations import NameTypeAwareAnnotation, find_annotation
from .request import RequestAdapter, RequestContributor
from .response import ResponseExtractor, mk_response_extractor

if typing.TYPE_CHECKING:
    from ..client_base import ClientBase
    from ..operation import Operation


def process_operation_method(fn: Callable, op: 'Operation') -> tuple[RequestAdapter, ResponseExtractor]:
    sig = inspect.signature(fn)
    try:
        response_extractor, media_types = mk_response_extractor(sig.return_annotation)
        request_adapter = prepare_request_adapter(fn.__name__, sig, op, media_types)
        return request_adapter, response_extractor
    except TypeError as error:
        raise TypeError(fn.__name__) from error


def prepare_request_adapter(name: str, sig: inspect.Signature, operation: 'Operation', accept: Iterable[str]) -> RequestAdapter:
    contributors = dict(process_param(param) for param in sig.parameters.values() if param.annotation != typing.Self)
    return RequestAdapter(
        name,
        operation.method,
        operation.path,
        contributors,
        accept,
        operation.security,
    )


def process_param(param: inspect.Parameter) -> tuple[str, RequestContributor]:
    name = param.name
    annotation = param.annotation

    if annotation is None:
        raise TypeError(f'{name}: Missing  type annotation')

    typ, annotation = find_annotation(annotation, RequestContributor)  # type: ignore[type-abstract]
    if isinstance(annotation, NameTypeAwareAnnotation):
        annotation.supply_formal(name, typ)
    return name, annotation


def mk_exchange_fn(
    request_adapter: RequestAdapter,
    response_handler: ResponseExtractor,
) -> 'Callable[..., Awaitable[typing.Any]]':
    async def exchange(self: 'ClientBase', **kwargs) -> typing.Any:
        request, auth = request_adapter.build_request(self, kwargs)

        response = await self._client.send(request, auth=auth)

        await response.aread()
        return response_handler.handle_response(response)

    return exchange


ResponseHandlerMapMut: typing.TypeAlias = dict[str, dict[str, dict[str, ResponseExtractor]]]
