import inspect
from collections.abc import Awaitable, Callable, Sequence

import httpx
import typing_extensions as typing

from ..middleware import HttpxMiddleware
from ..types_ import Next
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


def _wrap_middleware(mw_: HttpxMiddleware, next_: Next) -> Next:
    async def wrapped(req: httpx.Request) -> httpx.Response:
        return await mw_(req, next_)

    return wrapped


def _mk_final_send(client_send, auth: httpx.Auth) -> Next:
    async def send(request: httpx.Request) -> httpx.Response:
        resp = await client_send(request, auth=auth)
        await resp.aread()
        return resp

    return send


def mk_send(client_send, auth: httpx.Auth, middlewares: Sequence[HttpxMiddleware]) -> Next:
    send = _mk_final_send(client_send, auth)
    for middleware in reversed(middlewares):
        send = _wrap_middleware(middleware, send)

    return send


def mk_exchange_fn(
    op_method: Callable,
    op_decorator: 'Operation',
) -> Callable[..., Awaitable[typing.Any]]:
    request_adapter, response_handler = process_operation_method(op_method, op_decorator)

    async def exchange(self: 'ClientBase', **kwargs) -> typing.Any:
        request = request_adapter.build_request(self, kwargs)
        response = await self._send(request)
        status_code, result = response_handler.handle_response(response)
        if status_code >= 400:
            raise HttpErrorResponse(status_code, result[1], result[0])
        else:
            return result

    return exchange
