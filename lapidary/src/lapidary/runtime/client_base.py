__all__ = [
    'ClientBase',
]

import dataclasses
import logging
from abc import ABC
from functools import partial
from typing import Optional, Any, cast

import httpx
import pydantic

from .auth.common import AuthParamModel
from .load import load_yaml_cached_
from .model import get_client_class, ClientClass, OperationFunctionModel, get_resolver
from .module_path import ModulePath
from .openapi import OpenApiModel
from .request import build_request
from .response import ResponseMap, handle_response

logger = logging.getLogger(__name__)


class ClientBase(ABC):
    def __init__(self, base_url: Optional[str] = None, auth: Any = None):
        root = ModulePath(self.__module__).parent()

        openapi, client_model = load_model(str(root))

        if base_url is None and openapi.servers and len(openapi.servers) > 0:
            base_url = openapi.servers[0].url
        assert base_url is not None

        if auth is not None:
            # asdict returns deep-dict, here we need a shallow one
            auth_dict = {field.name: getattr(auth, field.name) for field in dataclasses.fields(auth)}
            auth_name, auth_factory = next(filter(lambda item: item[1] is not None, auth_dict.items()))
            auth_model = next(filter(lambda model: model.auth_name == auth_name, client_model.init_method.auth_models))

            auth_factory: AuthParamModel
            auth_handler = auth_factory.create(auth_model)
        else:
            auth_handler = None

        self._client = httpx.AsyncClient(auth=auth_handler, base_url=base_url)
        self._global_response_map = {
            status: {
                media_type: type_hint.resolve() for media_type, type_hint in media_map.items()
            }
            for status, media_map in client_model.init_method.response_map.items()
        }

        self._ops = {op.name: op for op in client_model.methods}

    def __getattr__(self, item: str):
        async def op_handler(op: OperationFunctionModel, request_body=None, **kwargs):
            if op.params_model_name:
                param_model = cast(pydantic.BaseModel, op.params_model_name.resolve()).parse_obj(kwargs)
            else:
                param_model = None

            response_map = {status: {mime: type_.resolve() for mime, type_ in mime_map.items()} for status, mime_map in op.response_map.items()}

            return await self._request(
                op.method,
                op.path.format(**kwargs),
                param_model=param_model,
                request_body=request_body,
                response_map=response_map,
                # auth=self.auth_tokenAuth,
            )

        return partial(op_handler, self._ops[item])

    async def __aenter__(self) -> 'ClientBase':
        await self._client.__aenter__()
        return self

    async def __aexit__(self, __exc_type=None, __exc_value=None, __traceback=None, ) -> Optional[bool]:
        return await self._client.__aexit__(__exc_type, __exc_value, __traceback)

    async def aclose(self) -> None:
        await self.__aexit__()

    async def _request(
            self,
            method: str,
            url: str,
            param_model: Optional[pydantic.BaseModel] = None,
            request_body: Any = None,
            response_map: Optional[ResponseMap] = None,
            auth: Optional[httpx.Auth] = httpx.USE_CLIENT_DEFAULT,
    ):
        request_ = build_request(param_model, request_body, response_map, self._global_response_map)
        request = self._client.build_request(method, url, **request_)

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("%s", f'{request.method} {request.url} {request.headers}')

        response = await self._client.send(request, auth=auth)

        return handle_response(response, response_map, self._global_response_map)


def load_model(mod: str) -> tuple[OpenApiModel, ClientClass]:
    from importlib.resources import open_text
    import sys
    module = sys.modules[mod]
    with open_text(module, 'openapi.yaml') as stream:
        text = stream.read()

    import platformdirs
    d = load_yaml_cached_(text, platformdirs.user_cache_path(), True)
    openapi = OpenApiModel.parse_obj(d)
    return openapi, get_client_class(openapi, ModulePath(mod), get_resolver(openapi, mod))
