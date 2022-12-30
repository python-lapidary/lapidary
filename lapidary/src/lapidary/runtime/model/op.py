import pkgutil
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Optional, Type

from .plugins import PagingPlugin
from .refs import ResolverFunc
from .response_map import get_response_map, ResponseMap
from .. import names
from ..module_path import ModulePath
from ..openapi import model as openapi, PluginModel
from ..openapi.utils import get_operations


@dataclass(frozen=True)
class OperationModel:
    method: str
    path: str
    params_model: Optional[Type]
    response_map: Optional[ResponseMap]
    paging: Optional[PagingPlugin]


def get_operation(
        op: openapi.Operation, method: str, url_path: str, module: ModulePath, resolver: ResolverFunc
) -> OperationModel:
    response_map = get_response_map(op.responses, op.operationId, module, resolver)

    return OperationModel(
        method=method,
        path=re.compile(r'\{([^}]+)\}').sub(r'{p_\1}', url_path),
        params_model=pkgutil.resolve_name(names.param_model_name(module, op.operationId)) if op.parameters else None,
        response_map=response_map,
        paging=instantiate_plugin(op.paging) if op.paging else None,
    )


def get_operation_functions(openapi_model: openapi.OpenApiModel, module: ModulePath, resolver: ResolverFunc) -> Mapping[str, OperationModel]:
    return {
        op.operationId: get_operation(op, method, url_path, module / 'paths' / op.operationId, resolver)
        for url_path, path_item in openapi_model.paths.items()
        for method, op in get_operations(path_item, True)
    }


def instantiate_plugin(model: Optional[PluginModel]) -> Optional[PagingPlugin]:
    type_ = pkgutil.resolve_name(model.factory)
    return type_()
