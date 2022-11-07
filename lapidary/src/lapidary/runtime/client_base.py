import functools
from collections.abc import Coroutine

import httpx

from . import ApiBase
from .load import load_yaml_cached_
from .model.client_class import get_client_class, ClientClass
from .model.operation_function import OperationFunctionModel
from .model.refs import get_resolver
from .module_path import ModulePath
from .openapi import OpenApiModel


class ClientBase(ApiBase):
    def __init__(self, **kwargs):
        root = ModulePath(self.__module__).parent()

        openapi, client_model = load_model(str(root))

        base_url = kwargs.pop('base_url', None)
        if base_url is None:
            base_url = openapi.servers[0].url

        super().__init__(httpx.AsyncClient(base_url=base_url))

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
