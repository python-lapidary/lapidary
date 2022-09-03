from .attribute import AttributeModel
from .attribute_annotation import get_attr_annotation
from .schema_class import SchemaClass
from .type_ref import TypeRef
from ..refs import ResolverFunc
from ...openapi import model as openapi


def get_param_attribute(param: openapi.Parameter, path: list[str], resolver: ResolverFunc) -> AttributeModel:
    return AttributeModel(
        name=param.name,
        annotation=get_attr_annotation(param.schema_, param.required, [*path, param.name], resolver),
        deprecated=param.deprecated,
    )


def get_param_model_class(
        operation: openapi.Operation,
        path: list[str],
        resolver: ResolverFunc,
) -> SchemaClass:
    attributes = [get_param_attribute(param, [*path, param.name], resolver) for param in
                  operation.parameters] if operation.parameters else []
    base_type = TypeRef.from_str('pydantic.BaseModel')

    return SchemaClass(
        class_name=path[-1],
        base_type=base_type,
        attributes=attributes,
        docstr=operation.description or None,
    )

