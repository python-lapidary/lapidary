import logging
import re
from dataclasses import dataclass
from typing import Optional, Union

import inflection

from .attribute import AttributeModel
from .attribute_annotation import AttributeAnnotationModel
from .refs import ResolverFunc
from ..module_path import ModulePath
from ..type_ref import TypeRef, get_type_ref
from ...openapi import model as openapi

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OperationFunctionModel:
    name: str
    method: str
    path: str
    params: list[AttributeModel]
    params_model_name: Optional[TypeRef]
    result_class_map: dict[str, TypeRef]
    docstr: Optional[str] = None


_FIELD_PROPS = dict(
    in_=None,
    description=None,
    allowEmptyValue=False,
    style=None,
    explode=None,
    allowReserved=False,
)


def get_operation_param(param: Union[openapi.Parameter, openapi.Reference], parent_name: str, module: ModulePath, resolve: ResolverFunc) -> AttributeModel:
    if isinstance(param, openapi.Reference):
        param, module, _ = resolve(param, openapi.Parameter)

    schema = param.schema_
    if isinstance(schema, openapi.Reference):
        schema, module, schema_name = resolve(schema, openapi.Schema)
    else:
        schema_name = inflection.camelize(parent_name) + inflection.camelize(param.name)
        module = module / 'schemas'

    field_props = {k: (getattr(param, k) or _FIELD_PROPS[k]) for k in _FIELD_PROPS}
    param_name = param.in_[0] + '_' + sanitise_param_name(param.name)

    field_props['alias'] = param.name

    return AttributeModel(
        name=param_name,
        annotation=AttributeAnnotationModel(
            type=get_type_ref(schema, module, schema_name, param.required, resolve),
            field_props=field_props,
        ),
        deprecated=param.deprecated,
    )


def sanitise_param_name(param_name: str) -> str:
    # potential name clash
    return re.compile(r'\W+').sub('_', param_name)


def resolve_type_ref(typ: Union[openapi.Schema, openapi.Reference], module: ModulePath, name: str, resolver: ResolverFunc) -> TypeRef:
    if isinstance(typ, openapi.Reference):
        typ, module, name = resolver(typ, openapi.Schema)
    return get_type_ref(typ, module, name, True, resolver)


def get_operation_func(op: openapi.Operation, method: str, url_path: str, module: ModulePath, resolver: ResolverFunc) -> OperationFunctionModel:
    params = [get_operation_param(oapi_param, op.operationId, module, resolver) for oapi_param in op.parameters] if op.parameters else []

    result_class_map = {
        resp_code: resolve_type_ref(list(typ.content.values())[0].schema_, module, inflection.camelize(op.operationId) + resp_code + 'Response', resolver)
        for resp_code, typ in op.responses.__root__.items()
        if typ.content
    }

    return OperationFunctionModel(
        name=op.operationId,
        method=method,
        path=re.compile(r'\{([^}]+)\}').sub(r'{p_\1}', url_path),
        params=params,
        params_model_name=TypeRef(module=(module / 'schemas').str(), name=inflection.camelize(op.operationId)) if op.parameters else None,
        result_class_map=result_class_map,
    )
