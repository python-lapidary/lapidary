from .attribute import AttributeModel, get_enum_attribute
from .attribute_annotation import AttributeAnnotationModel
from .schema_class_model import SchemaClass, ModelType
from ..type_ref import BuiltinTypeRef, TypeRef
from ...openapi import model as openapi


def check_named_attrs(schema: openapi.Schema) -> None:
    if schema.lapidary_enum_names is None:
        return
    for key, val in schema.lapidary_enum_names.items():
        if val not in schema.enum:
            raise ValueError('unknown value of', key)


def get_enum_value(value, schema: openapi.Schema) -> AttributeModel:
    if schema.lapidary_model_type is not None:
        import warnings
        warnings.warn('Enum schemas must not declare x-model-type')
    if value is None:
        name = 'none'
    elif value == '':
        name = 'empty'
    else:
        name = value
    value = "'" + value.replace("'", r"\'") + "'" if value is not None else None
    return AttributeModel(name, AttributeAnnotationModel(BuiltinTypeRef(name='__ignored__'), dict(default=value)))


def get_enum_class(
        schema: openapi.Schema,
        name: str
):
    check_named_attrs(schema)
    named_attrs = [get_enum_attribute(v, name) for name, v in schema.lapidary_enum_names.items()] if schema.lapidary_enum_names is not None else []
    unnamed_attrs = [get_enum_attribute(v) for v in schema.enum if schema.lapidary_enum_names is None or v not in schema.lapidary_enum_names.values()]

    return SchemaClass(
        class_name=name,
        base_type=TypeRef.from_str('enum.Enum'),
        attributes=[*named_attrs, *unnamed_attrs],
        docstr=schema.description or None,
        model_type=ModelType.enum,
    )
