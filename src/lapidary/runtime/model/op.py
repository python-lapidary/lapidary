from dataclasses import dataclass
from typing import Optional, Mapping, Any, List, cast, Iterator, Tuple

from .params import Param, get_param_model
from .plugins import PagingPlugin
from .refs import ResolverFunc
from .response_map import get_response_map, ResponseMap
from ..module_path import ModulePath
from ..openapi import model as openapi, PluginModel, get_operations


@dataclass(frozen=True)
class OperationModel:
    method: str
    path: str
    params: List[Param]
    response_map: ResponseMap
    paging: Optional[PagingPlugin]


def _resolve_name(name: str) -> Any:
    import sys
    if sys.version_info < (3, 9):
        from pkgutil_resolve_name import resolve_name  # type: ignore[import]
    else:
        from pkgutil import resolve_name

    return resolve_name(name)


def get_operation(
        op: openapi.Operation, method: str, url_path: str, module: ModulePath, resolver: ResolverFunc
) -> OperationModel:
    assert op.operationId
    response_map = get_response_map(op.responses, op.operationId, module, resolver)

    return OperationModel(
        method=method,
        path=url_path,
        params=[get_param_model(param, op, module, resolver) for param in op.parameters] if op.parameters else [],
        response_map=response_map,
        paging=instantiate_plugin(op.paging) if op.paging else None,
    )


def get_operation_functions(openapi_model: openapi.OpenApiModel, module: ModulePath, resolver: ResolverFunc) -> Mapping[str, OperationModel]:
    return {
        cast(str, op.operationId): get_operation(op, method, url_path, module / 'paths' / op.operationId, resolver)
        for url_path, path_item in openapi_model.paths.items()
        if isinstance(path_item, openapi.PathItem)
        for method, op in cast(Iterator[Tuple[str, openapi.Operation]], get_operations(path_item, True))
    }


def instantiate_plugin(model: PluginModel) -> PagingPlugin:
    type_ = _resolve_name(model.factory)
    return type_()
