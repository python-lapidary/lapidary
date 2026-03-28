from __future__ import annotations

from collections.abc import Awaitable, Callable, MutableMapping, Sequence

import httpx
import typing_extensions as typing

from .middleware import HttpxMiddleware
from .model.error import HttpErrorResponse
from .model.request import RequestAdapter
from .model.response import ResponseMessageExtractor
from .operation import mk_send as _mk_send, process_operation_method
from .types_ import Next, RequestFactory

API_T = typing.TypeVar('API_T')


def for_api(
    api: type[API_T],
    client: httpx.AsyncClient,
    base_url: str,
    *,
    middlewares: Sequence[HttpxMiddleware] = (),
    auth: httpx.Auth | None = None,
) -> APIClient[API_T]:
    """
    Create an :class:`APIClient` for the given API descriptor class.

    :param api: The API descriptor class — a plain class whose methods are decorated with :func:`get`, :func:`post`, etc.
    :param client: The underlying :class:`httpx.AsyncClient` used to send requests.
    :param base_url: Base URL prepended to all operation paths.
    :param middlewares: Optional sequence of :class:`HttpxMiddleware` instances applied to every request.
    :param auth: Optional :class:`httpx.Auth` instance used to authenticate requests.
    """
    api_model = APIModel(api)
    return APIClient(api_model, client, base_url, auth=auth, middlewares=middlewares)


class APIClient(typing.Generic[API_T]):
    def __init__(
        self,
        api_model: APIModel,
        client: httpx.AsyncClient,
        base_url: str,
        *,
        middlewares: Sequence[HttpxMiddleware] = (),
        auth: httpx.Auth | None = None,
    ) -> None:
        self._api_model = api_model
        self._auth = auth
        self._base_url = base_url
        self._client = client
        self._middlewares = middlewares

        send = _mk_send(client.send, auth, middlewares)
        request_factory = typing.cast(RequestFactory, client.build_request)
        self._ops = Dispatcher(send, request_factory, base_url, self._api_model)

    def with_auth(self, auth: httpx.Auth | None) -> typing.Self:
        return APIClient(
            self._api_model,
            self._client,
            self._base_url,
            middlewares=self._middlewares,
            auth=auth,
        )

    @property
    def ops(self) -> API_T:
        return self._ops


class Dispatcher:
    def __init__(
        self,
        send: Next,
        request_factory: RequestFactory,
        base_url: str,
        api_model: APIModel,
    ) -> None:
        self._send = send
        self._request_factory = request_factory
        self._base_url = base_url
        self._cache: MutableMapping[str, Callable[..., Awaitable]] = {}
        self._api_model = api_model

    def __getattr__(self, operation_id: str) -> Callable[..., Awaitable]:
        try:
            return self._cache[operation_id]
        except KeyError:
            op_adapter = self._api_model.get(operation_id)
            fn = op_adapter.bind(self._send, self._request_factory, self._base_url)
            self._cache[operation_id] = fn
            return fn


class OperationAdapter:
    def __init__(
        self,
        name: str,
        builder: RequestAdapter,
        extractor: ResponseMessageExtractor,
    ):
        self._name = name
        self._request_adapter = builder
        self._response_handler = extractor

    def bind(
        self,
        send: Next,
        request_factory: RequestFactory,
        base_url: str,
    ):
        async def fn(
            **kwargs,
        ):
            request = self._request_adapter.build_request(request_factory, base_url, kwargs)
            response = await send(request)
            status_code, result = self._response_handler.handle_response(response)
            if status_code >= 400:
                raise HttpErrorResponse(status_code, result[1], result[0])
            else:
                return result

        fn.__name__ = self._name
        return fn


class APIModel:
    """An equivalet of a class, in the sense that it holds a dictionary of operations,
    unbound from a specific connection and auth context."""

    def __init__(
        self,
        api_class: type[API_T],
    ):
        self._api_class = api_class
        self._adapters: dict[str, OperationAdapter] = {}

    def get(self, name: str) -> OperationAdapter:
        try:
            return self._adapters[name]
        except KeyError:
            op_fn = getattr(self._api_class, name)
            operation_id = op_fn.__name__
            request_adapter, response_handler = process_operation_method(op_fn, op_fn._lapidary_method, op_fn._lapidary_path)
            adapter = OperationAdapter(operation_id, request_adapter, response_handler)

            self._adapters[operation_id] = adapter
            return adapter
