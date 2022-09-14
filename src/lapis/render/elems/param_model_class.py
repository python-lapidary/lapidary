from typing import Generator

import inflection

from .attribute import AttributeModel
from .attribute_annotation import get_attr_annotation
from .refs import ResolverFunc
from .schema_class import SchemaClass, get_schema_classes
from ..module_path import ModulePath
from ..type_ref import TypeRef
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
    return AttributeModel(
        name=param.in_[0] + '_' + param.name.replace(':', '_'),
        annotation=get_attr_annotation(param.schema_, param.name, parent_name, param.required, module, resolver, param.in_),
        deprecated=param.deprecated,
    )


def get_param_model_classes(
        operation: openapi.Operation,
        name: str,
        module: ModulePath,
        resolver: ResolverFunc,
) -> Generator[SchemaClass, None, None]:
    schema_class = get_param_model_class(operation, name, module, resolver)
    if schema_class is not None:
        yield schema_class

    # handle sub schemas
    for param in operation.parameters:
        schema = param.schema_
        if not isinstance(schema, openapi.Schema):
            continue
        yield from get_schema_classes(schema, inflection.camelize(name) + inflection.camelize(param.name), module, resolver)


def get_param_model_class(
        operation: openapi.Operation,
        name: str,
        module: ModulePath,
        resolver: ResolverFunc,
) -> SchemaClass:
    attributes = [get_param_attribute(param, name, module, resolver) for param in
                  operation.parameters] if operation.parameters else []
    base_type = TypeRef.from_str('pydantic.BaseModel')

    return SchemaClass(
        class_name=inflection.camelize(name),
        base_type=base_type,
        attributes=attributes,
        docstr=operation.description or None,
    )
