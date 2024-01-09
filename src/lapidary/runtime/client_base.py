import abc
from collections.abc import Mapping
import logging

import httpx

from .auth import get_auth
from .compat import typing as ty
from .model.op import LapidaryOperation, get_operation_model
from .request import RequestFactory, build_request

logger = logging.getLogger(__name__)


class ClientBase(abc.ABC):
    def __init__(
            self,
            **kwargs,
    ):
        if 'base_url' not in kwargs:
            raise ValueError('Missing base_url.')

        self._client = httpx.AsyncClient(**kwargs)

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
