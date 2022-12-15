__all__ = [
    'ClientBase',
]

import logging
from abc import ABC
from functools import partial
from typing import Optional, Any, cast

import httpx
import pydantic

from .load import load_model
from .model import OperationModel, get_resolver, ResponseMap, get_client_model, get_api_responses
from .module_path import ModulePath
from .request import build_request, get_path
from .response import handle_response

logger = logging.getLogger(__name__)


class ClientBase(ABC):
    def __init__(self, base_url: Optional[str] = None, auth: Any = None):
        root = ModulePath(self.__module__).parent()

        openapi_model = load_model(str(root))
        model = get_client_model(openapi_model, root, get_resolver(openapi_model, str(root)))
        self._ops = model.methods

        if base_url is None and openapi_model.servers and len(openapi_model.servers) > 0:
            base_url = openapi_model.servers[0].url
        if base_url is None:
            raise ValueError('Missing base_url.')

        scheme_name, scheme = next(iter(auth.__dict__.items()))
        auth_handler = scheme.create(model.init_method.auth_models[scheme_name])

        self._client = httpx.AsyncClient(auth=auth_handler, base_url=base_url)
        self._api_responses = get_api_responses(openapi_model, root)

    def __getattr__(self, item: str):
        async def op_handler(op: OperationModel, request_body=None, **kwargs):
            if op.params_model:
                param_model = cast(pydantic.BaseModel, op.params_model).parse_obj(kwargs)
            else:
                param_model = None

            return await self._request(
                op.method,
                get_path(op.path, param_model),
                param_model=param_model,
                request_body=request_body,
                response_map=op.response_map,
                # auth=self.auth_tokenAuth,
            )

        return partial(op_handler, self._ops[item])

    async def __aenter__(self) -> 'ClientBase':
        await self._client.__aenter__()
        return self

    async def __aexit__(self, __exc_type=None, __exc_value=None, __traceback=None, ) -> Optional[bool]:
        return await self._client.__aexit__(__exc_type, __exc_value, __traceback)

    async def _request(
            self,
            method: str,
            url: str,
            param_model: Optional[pydantic.BaseModel] = None,
            request_body: Any = None,
            response_map: Optional[ResponseMap] = None,
            auth: Optional[httpx.Auth] = httpx.USE_CLIENT_DEFAULT,
    ):
        request_ = build_request(param_model, request_body, response_map, self._api_responses)
        request = self._client.build_request(method, url, **request_)

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("%s", f'{request.method} {request.url} {request.headers}')

        response = await self._client.send(request, auth=auth)

        return handle_response(response, response_map, self._api_responses)
