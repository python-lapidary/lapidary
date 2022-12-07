from dataclasses import dataclass, field

from lapidary.runtime import openapi
from lapidary.runtime.model.refs import ResolverFunc
from lapidary.runtime.module_path import ModulePath
from lapidary.runtime.openapi.utils import get_operations

from .client_init import ClientInit, get_client_init
from .operation_function import OperationFunctionModel, get_operation_func


@dataclass(frozen=True)
class ClientClass:
    init_method: ClientInit
    methods: list[OperationFunctionModel] = field(default_factory=list)


def get_client_class(openapi_model: openapi.OpenApiModel, module: ModulePath, resolver: ResolverFunc) -> ClientClass:
    functions = [
        get_operation_func(op, method, url_path, module / 'paths' / op.operationId, resolver)
        for url_path, path_item in openapi_model.paths.__root__.items()
        for method, op in get_operations(path_item, True)
    ]

    return ClientClass(
        init_method=get_client_init(openapi_model, module, resolver),
        methods=functions,
    )
