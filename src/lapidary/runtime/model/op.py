from dataclasses import dataclass
from typing import Optional, Mapping, Any, List, cast, Iterator, Tuple

from .params import Param, get_param_model
from .plugins import PagingPlugin
from .refs import ResolverFunc
from .response_map import get_response_map, ResponseMap
from ..module_path import ModulePath
from ..names import get_ops_module
from ..openapi import model as openapi, PluginModel, get_operations


@dataclass(frozen=True)
class OperationModel:
    method: str
    path: str
    params: List[Param]
    response_map: ResponseMap
    paging: Optional[PagingPlugin]


def _resolve_name(name: str) -> Any:
    from pkgutil import resolve_name

    return resolve_name(name)


def get_operation(
        operation: openapi.Operation, method: str, url_path: str, parent_module: ModulePath, resolver: ResolverFunc
) -> OperationModel:
    assert operation.operationId

    module = parent_module / operation.operationId
    response_map = get_response_map(operation.responses, module / "responses", resolver)

    return OperationModel(
        method=method,
        path=url_path,
        params=[
            get_param_model(param, operation, module, resolver)
            for param in operation.parameters
        ] if operation.parameters else [],
        response_map=response_map,
        paging=instantiate_plugin(operation.paging) if operation.paging else None,
    )


def get_operation_functions(
        openapi_model: openapi.OpenApiModel, module: ModulePath, resolver: ResolverFunc
) -> Mapping[str, OperationModel]:
    return {
        cast(str, op.operationId): get_operation(op, method, url_path, get_ops_module(module), resolver)
        for url_path, path_item in openapi_model.paths.items()
        if isinstance(path_item, openapi.PathItem)
        for method, op in cast(Iterator[Tuple[str, openapi.Operation]], get_operations(path_item, True))
    }


def instantiate_plugin(model: PluginModel) -> PagingPlugin:
    type_ = _resolve_name(model.factory)
    return type_()
