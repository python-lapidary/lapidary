from collections.abc import Mapping
from dataclasses import dataclass, field

from .client_init import get_client_init, ClientInit
from .op import OperationModel, get_operation_functions
from .refs import ResolverFunc
from ..module_path import ModulePath
from ..openapi import model as openapi


@dataclass(frozen=True)
class ClientModel:
    init_method: ClientInit
    methods: Mapping[str, OperationModel] = field(default_factory=dict)


def get_client_model(openapi_model: openapi.OpenApiModel, module: ModulePath, resolve: ResolverFunc) -> ClientModel:
    return ClientModel(
        init_method=get_client_init(openapi_model, module, resolve),
        methods=get_operation_functions(openapi_model, module, resolve),
    )
