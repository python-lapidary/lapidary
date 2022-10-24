from typing import Generator

from .attribute import AttributeModel
from .attribute_annotation import get_attr_annotation
from .refs import ResolverFunc
from .schema_class import get_schema_classes
from .schema_class_model import SchemaClass, ModelType
from .type_hint import TypeHint
from ..module_path import ModulePath
from ..names import get_subtype_name
from ...openapi import model as openapi

"""
Param model is a synthetic (from the perspective of OpenAPI specification) object that holds and validates all Operation parameters.
"""


def get_param_attribute(
        param: openapi.Parameter,
        parent_name: str,
        module: ModulePath,
        resolver: ResolverFunc,
) -> AttributeModel:
    param_name = param.lapidary_name or param.name
    return AttributeModel(
        name=param.in_[0] + '_' + param_name,
        annotation=get_attr_annotation(
            param.schema_, param_name, parent_name, param.required, module, resolver, param.in_
        ),
        deprecated=param.deprecated,
    )


def get_param_model_classes(
        operation: openapi.Operation,
        name: str,
        module: ModulePath,
        resolver: ResolverFunc,
) -> Generator[SchemaClass, None, None]:
    # handle sub schemas
    for param in operation.parameters:
        schema = param.schema_
        if not isinstance(schema, openapi.Schema):
            continue
        param_name = param.lapidary_name or param.name
        yield from get_schema_classes(schema, get_subtype_name(name, param_name), module, resolver)

    schema_class = get_param_model_class(operation, name, module, resolver)
    if schema_class is not None:
        yield schema_class


def get_param_model_class(
        operation: openapi.Operation,
        name: str,
        module: ModulePath,
        resolver: ResolverFunc,
) -> SchemaClass:
    attributes = [get_param_attribute(param, name, module, resolver) for param in
                  operation.parameters] if operation.parameters else []
    base_type = TypeHint.from_str('pydantic.BaseModel')

    return SchemaClass(
        class_name=name,
        base_type=base_type,
        attributes=attributes,
        docstr=operation.description or None,
        model_type=ModelType.param_model,
        has_aliases=True,
    )
