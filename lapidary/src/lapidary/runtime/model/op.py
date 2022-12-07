import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Optional, Type

import inflection

from .refs import ResolverFunc
from .response_map import get_response_map, ResponseMap
from ..module_path import ModulePath
from ..names import PARAM_MODEL
from ..openapi import model as openapi
from ..openapi.utils import get_operations
from ..types import resolve


@dataclass(frozen=True)
class OperationModel:
    method: str
    path: str
    params_model: Optional[Type]
    response_map: Optional[ResponseMap]


def get_operation(
        op: openapi.Operation, method: str, url_path: str, module: ModulePath, resolver: ResolverFunc
) -> OperationModel:

    response_map = get_response_map(op.responses, op.operationId, module, resolver)

    return OperationModel(
        method=method,
        path=re.compile(r'\{([^}]+)\}').sub(r'{p_\1}', url_path),
        params_model=resolve((module / PARAM_MODEL).str(), inflection.camelize(op.operationId)) if op.parameters else None,
        response_map=response_map,
    )


def get_operation_functions(openapi_model: openapi.OpenApiModel, module: ModulePath, resolver: ResolverFunc) -> Mapping[str, OperationModel]:
    return {
        op.operationId: get_operation(op, method, url_path, module / 'paths' / op.operationId, resolver)
        for url_path, path_item in openapi_model.paths.__root__.items()
        for method, op in get_operations(path_item, True)
    }
