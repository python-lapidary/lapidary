import abc
import logging
from collections.abc import Mapping
from importlib.metadata import version

import httpx
import typing_extensions as typing

from .model.op import OperationModel, get_operation_model
from .request import build_request

logger = logging.getLogger(__name__)

USER_AGENT = f'lapidary/{version("lapidary")}'


class ClientBase(abc.ABC):
    def __init__(
        self,
        base_url: str,
        user_agent: typing.Optional[str] = USER_AGENT,
        _http_client: typing.Optional[httpx.AsyncClient] = None,
        **httpx_kwargs,
    ):
        headers = httpx.Headers(httpx_kwargs.pop('headers', None)) or httpx.Headers()
        if user_agent:
            headers['User-Agent'] = user_agent

        self._client = _http_client or httpx.AsyncClient(base_url=base_url, headers=headers, **httpx_kwargs)
        self._lapidary_operations: typing.MutableMapping[str, OperationModel] = {}

    async def __aenter__(self):
        await self._client.__aenter__()
        return self

    async def __aexit__(self, __exc_type=None, __exc_value=None, __traceback=None) -> None:
        await self._client.__aexit__(__exc_type, __exc_value, __traceback)

    async def _request(
        self,
        method: str,
        path: str,
        fn: typing.Callable[..., typing.Awaitable],
        actual_params: Mapping[str, typing.Any],
    ):
        if fn.__name__ not in self._lapidary_operations:
            operation = get_operation_model(method, path, fn)
            self._lapidary_operations[fn.__name__] = operation
        else:
            operation = self._lapidary_operations[fn.__name__]

        request, auth = build_request(
            operation,
            actual_params,
            self._client.build_request,
        )

        logger.debug('%s %s %s', request.method, request.url, request.headers)

        response = await self._client.send(request, auth=auth)
        await response.aread()

        return operation.handle_response(response)
