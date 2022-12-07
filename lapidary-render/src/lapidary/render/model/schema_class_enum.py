from lapidary.runtime import openapi
from lapidary.render.model import get_enum_attribute
from lapidary.runtime.model.type_hint import TypeHint

from .schema_class_model import SchemaClass, ModelType


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
