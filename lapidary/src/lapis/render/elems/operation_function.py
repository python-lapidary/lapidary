import logging
import re
from dataclasses import dataclass

from typing import Optional, Union, Generator

from .attribute import AttributeModel
from .attribute_annotation import AttributeAnnotationModel
from .type_ref import TypeRef, get_type_ref
from ..refs import ResolverFunc
from ...openapi import model as openapi

logger = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class ParamModel(AttributeModel):
    required: bool


@dataclass(frozen=True)
class OperationFunctionModel:
    name: str
    method: str
    path: str
    params: list[ParamModel]
    params_model_name: Optional[TypeRef]
    result_class_map: dict[str, TypeRef]
    docstr: Optional[str] = None


def get_operation_param(param: Union[openapi.Parameter, openapi.Reference], path: list[str], resolver: ResolverFunc) -> ParamModel:
    if isinstance(param, openapi.Reference):
        param, path = resolver(param)

    schema = param.schema_
    if isinstance(schema, openapi.Reference):
        schema, schema_path = resolver(schema)
    else:
        schema_path = path

    field_props = {}
    param_name = param.in_[0] + '_' + sanitise_param_name(param.name)

    field_props['alias'] = param.name

    return ParamModel(
        name=param_name,
        annotation=AttributeAnnotationModel(
            type=get_type_ref(schema, param.required, schema_path, resolver),
            field_props=field_props,
        ),
        deprecated=param.deprecated,
        required=param.required,
    )


def sanitise_param_name(param_name: str) -> str:
    # potential name clash
    return re.compile(r'\W+').sub('_', param_name)


def get_param_model_name(path: list[str]) -> TypeRef:
    return get_type_ref(openapi.Schema(type=openapi.Type.object, ), True, [*path, 'Param'], None)


def resolve_type_ref(typ: Union[openapi.Schema, openapi.Reference], path: list[str], resolver: ResolverFunc) -> TypeRef:
    if isinstance(typ, openapi.Reference):
        typ, path = resolver(typ)
    return get_type_ref(typ, True, path, resolver)


def get_operation_func(op: openapi.Operation, method: str, url_path: str, path: list[str], resolver: ResolverFunc) -> OperationFunctionModel:
    url_path = re.compile(r'\{([^}]+)\}').sub(r'{p_\1}', url_path)
    return OperationFunctionModel(
        name=op.operationId,
        method=method,
        path=url_path,
        params=[get_operation_param(oapi_param, [*path, oapi_param.name], resolver) for oapi_param in op.parameters] if op.parameters else [],
        params_model_name=get_param_model_name(path),
        result_class_map={code: resolve_type_ref(list(typ.content.values())[0].schema_, [*path, code], resolver) for code, typ in op.responses.__root__.items()
                          if typ.content},
    )


def get_path_op_funcs(p: openapi.PathItem, path: list[str], resolver: ResolverFunc) -> Generator[OperationFunctionModel, None, None]:
    url_path = path[-1]
    if p.ref_:
        p, path = resolver(openapi.Reference(ref=p.ref_))

    for op_name in p.__fields_set__:
        v = getattr(p, op_name)
        if not isinstance(v, openapi.Operation):
            continue
        v: openapi.Operation
        op_path = [*path[:-1], v.operationId, op_name] if v.operationId else [*path, op_name]
        yield get_operation_func(v, op_name, url_path, op_path, resolver)
