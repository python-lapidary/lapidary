import abc
from collections.abc import Mapping
from importlib.metadata import version
import logging

import httpx

from .auth import get_auth
from .compat import typing as ty
from .model.op import LapidaryOperation, get_operation_model
from .request import RequestFactory, build_request

logger = logging.getLogger(__name__)

lapidary_ua = f'lapidary/{version("lapidary")}'


class ClientBase(abc.ABC):
    def __init__(
            self,
            user_agent: str = lapidary_ua,
            **httpx_kwargs,
    ):
        if 'base_url' not in httpx_kwargs:
            raise ValueError('Missing base_url.')

        headers = httpx.Headers(httpx_kwargs.pop('headers', None))
        headers = _mk_headers(headers, user_agent)

        self._client = httpx.AsyncClient(**httpx_kwargs, headers=headers)

    async def __aenter__(self):
        await self._client.__aenter__()
        return self

    async def __aexit__(self, __exc_type=None, __exc_value=None, __traceback=None) -> None:
        await self._client.__aexit__(__exc_type, __exc_value, __traceback)

    async def _request(
            self,
            fn: LapidaryOperation,
            actual_params: Mapping[str, ty.Any],
    ):
        if not fn.lapidary_operation_model:
            operation = get_operation_model(fn)
            fn.lapidary_operation_model = operation
        else:
            operation = fn.lapidary_operation_model

        request = build_request(
            operation,
            actual_params,
            ty.cast(RequestFactory, self._client.build_request),
        )

        logger.debug("%s %s %s", request.method, request.url, request.headers)

        response = await self._client.send(request, auth=get_auth(actual_params))
        return operation.handle_response(response)


def _mk_headers(
        headers: httpx.Headers,
        ua: str,
) -> httpx.Headers:
    if 'User-Agent' not in headers:
        if 'lapidary' not in ua:
            ua = f'{ua}; {lapidary_ua}'
        headers['User-Agent'] = ua

    return headers
