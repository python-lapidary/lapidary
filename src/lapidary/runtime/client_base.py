__all__ = [
    'ClientBase',
]

import logging
from abc import ABC
from functools import partial
from typing import Optional, Any, cast, Callable

import httpx
import pydantic

from .load import get_model
from .model import OperationModel, ClientModel
from .request import build_request, get_path
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
            self._model = get_model(self.__module__)

        if base_url is None:
            base_url = self._model.init_method.base_url
        if base_url is None:
            raise ValueError('Missing base_url.')

        scheme_name, scheme = next(iter(auth.__dict__.items())) if auth else (None, None)
        auth_handler = scheme.create(self._model.init_method.auth_models[scheme_name]) if scheme else None

        self._client = httpx.AsyncClient(auth=auth_handler, base_url=base_url, app=_app)

    def __getattr__(self, item: str):
        async def op_handler(op: OperationModel, request_body=None, **kwargs):
            if op.params_model:
                param_model = cast(pydantic.BaseModel, op.params_model).parse_obj(kwargs)
            else:
                param_model = None

            return await self._request(
                op,
                get_path(op.path, param_model),
                param_model=param_model,
                request_body=request_body,
            )

        return partial(op_handler, self._model.methods[item])

    async def __aenter__(self):
        await self._client.__aenter__()
        return self

    async def __aexit__(self, __exc_type=None, __exc_value=None, __traceback=None) -> Optional[bool]:
        return await self._client.__aexit__(__exc_type, __exc_value, __traceback)

    async def _request(
            self,
            operation: OperationModel,
            url: str,
            param_model: Optional[pydantic.BaseModel],
            request_body: Any,
            auth: Optional[httpx.Auth] = httpx.USE_CLIENT_DEFAULT,
    ):
        request_ = build_request(param_model, request_body, operation.response_map, self._model.init_method.response_map)
        request = self._client.build_request(operation.method, url, **request_)

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("%s", f'{request.method} {request.url} {request.headers}')

        response_handler = partial(handle_response, operation.response_map, self._model.init_method.response_map)

        if operation.paging:
            return mk_generator(operation.paging, request, auth, self._client, response_handler)

        response = await self._client.send(request, auth=auth)
        return response_handler(response)
