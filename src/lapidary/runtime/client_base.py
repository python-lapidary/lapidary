from abc import ABC
from collections.abc import Callable, Mapping
from functools import partial
import logging

import httpx
import typing_extensions as ty

from .model import ResponseMap
from .model.op import LapidaryOperation, get_operation_model
from .request import RequestFactory, build_request
from .response import handle_response

logger = logging.getLogger(__name__)


class ClientBase(ABC):
    def __init__(
            self,
            response_map: ResponseMap = None,
            *,
            _app: ty.Optional[Callable[..., ty.Any]] = None,
            **kwargs,
    ):
        self._response_map = response_map or {}
        if 'base_url' not in kwargs:
            raise ValueError('Missing base_url.')

        self._client = httpx.AsyncClient( app=_app, **kwargs)

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

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("%s", f'{request.method} {request.url} {request.headers}')

        response_handler = partial(handle_response, operation.response_map)

        auth = get_auth(actual_params)

        response = await self._client.send(request, auth=auth)
        return response_handler(response)


def get_auth(params: Mapping[str, ty.Any]) -> ty.Optional[httpx.Auth]:
    auth_params = [value for value in params.values() if isinstance(value, httpx.Auth)]
    auth_num = len(auth_params)
    if auth_num == 0:
        return None
    elif auth_num == 1:
        return auth_params[0]
    else:
        from httpx_auth.authentication import _MultiAuth
        return _MultiAuth(*auth_params)
