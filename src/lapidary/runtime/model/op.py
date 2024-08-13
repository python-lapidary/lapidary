import inspect
from collections.abc import Awaitable, Callable

import typing_extensions as typing

from .error import HttpErrorResponse
from .request import RequestAdapter, prepare_request_adapter
from .response import ResponseMessageExtractor, mk_response_extractor

if typing.TYPE_CHECKING:
    from ..client_base import ClientBase
    from ..operation import Operation


def process_operation_method(fn: Callable, op: 'Operation') -> tuple[RequestAdapter, ResponseMessageExtractor]:
    sig = inspect.signature(fn)
    try:
        response_extractor, media_types = mk_response_extractor(sig.return_annotation)
        request_adapter = prepare_request_adapter(fn.__name__, sig, op, media_types)
        return request_adapter, response_extractor
    except TypeError as error:
        raise TypeError(fn.__name__) from error


def mk_exchange_fn(
    op_method: Callable,
    op_decorator: 'Operation',
) -> Callable[..., Awaitable[typing.Any]]:
    request_adapter, response_handler = process_operation_method(op_method, op_decorator)

    async def exchange(self: 'ClientBase', **kwargs) -> typing.Any:
        request, auth = request_adapter.build_request(self, kwargs)

        response = await self._client.send(request, auth=auth)

        await response.aread()
        status_code, result = response_handler.handle_response(response)
        if status_code >= 400:
            raise HttpErrorResponse(status_code, result[1], result[0])
        else:
            return result

    return exchange
