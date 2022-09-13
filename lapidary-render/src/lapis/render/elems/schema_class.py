import logging
from dataclasses import dataclass, field
from typing import Optional, Generator

import inflection

from .attribute import AttributeModel, get_attributes, get_enum_attribute
from .attribute_annotation import AttributeAnnotationModel
from .refs import ResolverFunc
from ..module_path import ModulePath
from ..type_ref import TypeRef, BuiltinTypeRef
from ...openapi import model as openapi

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SchemaClass:
    class_name: str
    base_type: TypeRef
    docstr: Optional[str] = None
    attributes: list[AttributeModel] = field(default_factory=list)


def get_schema_classes(
        schema: openapi.Schema,
        name: str,
        module: ModulePath,
        resolver: ResolverFunc,
) -> Generator[SchemaClass, None, None]:
    if schema.enum is not None:
        yield get_enum_class(schema, name)
        name = name + 'Value'

    schema_class = get_schema_class(schema, name, module, resolver)
    if schema_class is not None:
        yield schema_class

    # handle sub schemas

    if schema.type is openapi.Type.array:
        item_schema = schema.items
        if isinstance(item_schema, openapi.Schema):
            yield from get_schema_classes(item_schema, name + 'Item', module, resolver)
    elif schema.type is openapi.Type.object:
        if schema.properties:
            for prop_name, prop_schema in schema.properties.items():
                if not isinstance(prop_schema, openapi.Schema):
                    continue
                yield from get_schema_classes(prop_schema, name + inflection.camelize(prop_name), module, resolver)


def get_schema_class(
        schema: openapi.Schema,
        name: str,
        module: ModulePath,
        resolver: ResolverFunc,
) -> Optional[SchemaClass]:
    if schema.type is not openapi.Type.object:
        return None

    logger.debug(name)

    base_type = TypeRef.from_str('pydantic.BaseModel')
    attributes = get_attributes(schema, name, module, resolver) if schema.properties else []

    return SchemaClass(
        class_name=name,
        base_type=base_type,
        attributes=attributes,
        docstr=schema.description or None,
    )


def get_enum_class(
        schema: openapi.Schema,
        name: str
):
    return SchemaClass(
        class_name=name,
        base_type=TypeRef.from_str('enum.Enum'),
        attributes=[get_enum_attribute(v) for v in schema.enum],
        docstr=schema.description or None,
    )


def get_enum_value(value, schema: openapi.Schema) -> AttributeModel:
    # if schema.type == openapi.Type.string:
    if value is None:
        name = 'none'
    elif value == '':
        name = 'empty'
    else:
        name = value
    value = "'" + value.replace("'", r"\'") + "'" if value is not None else None
    return AttributeModel(name, AttributeAnnotationModel(BuiltinTypeRef(name='__ignored__'), dict(default=value)))
