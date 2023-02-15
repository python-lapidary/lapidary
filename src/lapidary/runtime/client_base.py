__all__ = [
    'ClientBase',
]

import logging
from abc import ABC
from functools import partial
from typing import Optional, Any, Callable, Mapping

import httpx

from .auth.common import AuthT
from .load import get_model
from .model import OperationModel, ClientModel
from .module_path import ModulePath
from .request import build_request
from .response import handle_response, mk_generator

logger = logging.getLogger(__name__)


class ClientBase(ABC):
    def __init__(
            self,
            base_url: Optional[str] = None,
            auth: Any = None,
            *,
            _model: Optional[ClientModel] = None,
            _app: Optional[Callable[..., Any]] = None,
    ):
        if _model:
            self._model = _model
        else:
            self._model = get_model(ModulePath(self.__module__).parent())

        if base_url is None:
            base_url = self._model.base_url
        if base_url is None:
            raise ValueError('Missing base_url.')

        if auth and auth.__dict__:
            scheme_name, scheme = next(iter(auth.__dict__.items()))
            auth_handler = scheme.create(self._model.auth_models[scheme_name])
        else:
            auth_handler = None

        self._client = httpx.AsyncClient(auth=auth_handler, base_url=base_url, app=_app)

    def __getattr__(self, item: str):
        async def op_handler(op: OperationModel, request_body=None, **kwargs):
            return await self._request(
                op,
                actual_params=kwargs,
                request_body=request_body,
            )

        return partial(op_handler, self._model.methods[item])

    async def __aenter__(self):
        await self._client.__aenter__()
        return self

    async def __aexit__(self, __exc_type=None, __exc_value=None, __traceback=None) -> Optional[bool]:
        await self._client.__aexit__(__exc_type, __exc_value, __traceback)
        return None

    async def _request(
            self,
            operation: OperationModel,
            actual_params: Mapping[str, Any],
            request_body: Any,
            auth: AuthT = httpx.USE_CLIENT_DEFAULT,
    ):
        request = build_request(
            operation,
            actual_params,
            request_body,
            operation.response_map,
            self._model.response_map,
            self._client.build_request
        )

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("%s", f'{request.method} {request.url} {request.headers}')

        response_handler = partial(handle_response, operation.response_map, self._model.response_map)

        if operation.paging:
            return mk_generator(operation.paging, request, auth, self._client, response_handler)

        response = await self._client.send(request, auth=auth)
        return response_handler(response)