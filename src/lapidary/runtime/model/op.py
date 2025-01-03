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
    type_hints = typing.get_type_hints(fn, include_extras=True)
    params = {name: param.replace(annotation=type_hints[name]) for name, param in sig.parameters.items()}
    try:
        response_extractor, media_types = mk_response_extractor(type_hints['return'])
        request_adapter = prepare_request_adapter(fn.__name__, params, op, media_types)
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

        mw_state = []
        for mw in self._middlewares:
            mw_state.append(await mw.handle_request(request))

        response = await self._client.send(request, auth=auth)

        await response.aread()

        for mw, state in zip(reversed(self._middlewares), reversed(mw_state)):
            await mw.handle_response(response, request, state)

        status_code, result = response_handler.handle_response(response)
        if status_code >= 400:
            raise HttpErrorResponse(status_code, result[1], result[0])
        else:
            return result

    return exchange
