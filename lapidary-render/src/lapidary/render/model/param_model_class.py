"""
Param model is a synthetic (from the perspective of OpenAPI specification) object that holds and validates all Operation
parameters.
"""
from collections.abc import Iterator

import inflection
from lapidary.runtime import openapi
from lapidary.runtime.model.refs import ResolverFunc
from lapidary.runtime.model.type_hint import TypeHint
from lapidary.runtime.module_path import ModulePath
from lapidary.runtime.names import get_subtype_name, maybe_mangle_name, check_name

from .attribute import AttributeModel
from .attribute_annotation import get_attr_annotation
from .schema_class import get_schema_classes
from .schema_class_model import ModelType, SchemaClass


def get_param_attribute(
        param: openapi.Parameter,
        parent_name: str,
        module: ModulePath,
        resolver: ResolverFunc,
) -> AttributeModel:
    attr_name = maybe_mangle_name(param.in_[0] + '_' + (param.lapidary_name or param.name))
    check_name(attr_name)

    return AttributeModel(
        name=attr_name,
        annotation=get_attr_annotation(
            param.schema_, param.name, parent_name, param.required, module, resolver, param.in_
        ),
        deprecated=param.deprecated,
    )


def get_param_model_classes(
        operation: openapi.Operation,
        module: ModulePath,
        resolver: ResolverFunc,
) -> Iterator[SchemaClass]:
    # handle sub schemas
    for param in operation.parameters:
        schema = param.schema_
        if not isinstance(schema, openapi.Schema):
            continue
        param_name = param.lapidary_name or param.name
        yield from get_schema_classes(schema, get_subtype_name(operation.operationId, param_name), module, resolver)

    schema_class = get_param_model_class(operation, module, resolver)
    if schema_class is not None:
        yield schema_class


def get_param_model_class(
        operation: openapi.Operation,
        module: ModulePath,
        resolver: ResolverFunc,
) -> SchemaClass:
    attributes = [get_param_attribute(param, operation.operationId, module, resolver) for param in
                  operation.parameters] if operation.parameters else []
    base_type = TypeHint.from_str('pydantic.BaseModel')

    return SchemaClass(
        class_name=get_param_model_class_name(operation.operationId),
        base_type=base_type,
        attributes=attributes,
        docstr=operation.description or None,
        model_type=ModelType.param_model,
        has_aliases=True,
    )


def get_param_model_class_name(operation_id: str) -> str:
    return inflection.camelize(operation_id)
