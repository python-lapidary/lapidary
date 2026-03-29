import inspect
from collections.abc import Callable, Sequence

import httpx
import typing_extensions as typing

from .middleware import HttpxMiddleware
from .model.request import RequestAdapter, RequestObjectContributor
from .model.response import ResponseMessageExtractor, mk_response_extractor
from .types_ import Next

P = typing.ParamSpec('P')
R = typing.TypeVar('R')
OperationMethod: typing.TypeAlias = typing.Callable[P, R]


class MethodProto(typing.Protocol):
    def __call__(self, path: str) -> typing.Callable[[OperationMethod], OperationMethod]:
        pass


def op_decorator(http_method: str) -> MethodProto:
    def decorator(
        http_path: str,
        security: typing.Any = None,  # deprecated, ignored, TODO remove
    ):
        def wrapper(fn: OperationMethod) -> OperationMethod:
            fn._lapidary_method = http_method
            fn._lapidary_path = http_path
            return fn

        return wrapper

    return decorator


get = op_decorator('GET')
put = op_decorator('PUT')
post = op_decorator('POST')
delete = op_decorator('DELETE')
head = op_decorator('HEAD')
patch = op_decorator('PATCH')
trace = op_decorator('TRACE')


def process_operation_method(fn: Callable, method: str, path: str) -> tuple[RequestAdapter, ResponseMessageExtractor]:
    sig = inspect.signature(fn)
    type_hints = typing.get_type_hints(fn, include_extras=True)
    params = {name: param.replace(annotation=type_hints[name]) for name, param in sig.parameters.items()}
    try:
        response_extractor, media_types = mk_response_extractor(type_hints['return'])
        request_adapter = RequestAdapter(
            fn.__name__,
            method,
            path,
            RequestObjectContributor.for_signature(params),
            media_types,
        )
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


def mk_send(client_send, auth: httpx.Auth | None, middlewares: Sequence[HttpxMiddleware]) -> Next:
    send = _mk_final_send(client_send, auth)
    for middleware in reversed(middlewares):
        send = _wrap_middleware(middleware, send)

    return send
