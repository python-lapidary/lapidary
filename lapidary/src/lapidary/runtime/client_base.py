import dataclasses
from functools import partial
from typing import Optional, Any

import httpx

from . import ApiBase
from .auth.common import AuthParamModel
from .load import load_yaml_cached_
from .model.client_class import get_client_class, ClientClass
from .model.operation_function import OperationFunctionModel
from .model.refs import get_resolver
from .module_path import ModulePath
from .openapi import OpenApiModel


class ClientBase(ApiBase):
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

        client = httpx.AsyncClient(auth=auth_handler, base_url=base_url)
        super().__init__(client)

        self._ops = {op.name: op for op in client_model.methods}


    def _handle_call(self, name: str, request_body=None, **kwargs) -> Coroutine:
        async def op_handler(op: OperationFunctionModel):
            if op.params_model_name:
                param_model = op.params_model_name.resolve().parse_obj(kwargs)
            else:
                param_model = None

            response_map = {status: {mime: type.resolve() for mime, type in mime_map.items()} for status, mime_map in op.response_map.items()}

            return await self._request(
                op.method,
                op.path.format(**kwargs),
                param_model=param_model,
                request_body=request_body,
                response_map=response_map,
                # auth=self.auth_tokenAuth,
            )

        return op_handler(self._ops[name])

    def __getattr__(self, item: str):
        return functools.partial(self._handle_call, item)


def load_model(mod: str) -> tuple[OpenApiModel, ClientClass]:
    from importlib.resources import files
    import sys
    module = sys.modules[mod]
    with files(module).joinpath('openapi.yaml').open('r') as stream:
        text = stream.read()

    import platformdirs
    d = load_yaml_cached_(text, platformdirs.user_cache_path(), True)
    openapi = OpenApiModel.parse_obj(d)
    return openapi, get_client_class(openapi, ModulePath(mod), get_resolver(openapi, mod))
