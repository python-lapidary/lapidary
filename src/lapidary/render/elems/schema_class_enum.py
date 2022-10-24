from .attribute import AttributeModel, get_enum_attribute
from .attribute_annotation import AttributeAnnotationModel
from .schema_class_model import SchemaClass, ModelType
from .type_hint import BuiltinTypeHint, TypeHint
from ...openapi import model as openapi


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
    return AttributeModel(name, AttributeAnnotationModel(BuiltinTypeHint(name='__ignored__'), dict(default=value)))


def get_enum_class(
        schema: openapi.Schema,
        name: str
):
    return SchemaClass(
        class_name=name,
        base_type=TypeHint.from_str('enum.Enum'),
        attributes=[get_enum_attribute(v, schema.lapidary_names.get(v, v)) for v in schema.enum],
        docstr=schema.description or None,
        model_type=ModelType.enum,
    )
