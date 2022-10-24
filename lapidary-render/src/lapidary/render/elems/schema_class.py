import logging
from typing import Optional, Generator

from .attribute import get_attributes
from .refs import ResolverFunc
from .schema_class_enum import get_enum_class
from .schema_class_model import SchemaClass, ModelType
from .type_hint import BuiltinTypeHint, TypeHint
from ..module_path import ModulePath
from ..names import get_subtype_name
from ...openapi import model as openapi

logger = logging.getLogger(__name__)


def get_schema_classes(
        schema: openapi.Schema,
        name: str,
        module: ModulePath,
        resolver: ResolverFunc,
) -> Generator[SchemaClass, None, None]:
    # First handle the enum case, so that the model class has suffixed name, and all sub-schemas use it as their prefix
    if schema.enum is not None:
        enum_class = get_enum_class(schema, name)
        name = name + 'Value'
    else:
        enum_class = None

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
                prop_name = prop_schema.lapidary_name or schema.lapidary_names.get(prop_name, prop_name)
                yield from get_schema_classes(prop_schema, get_subtype_name(name, prop_name), module, resolver)
    for key in ['oneOf', 'anyOf', 'allOf']:
        inheritance_elem = getattr(schema, key)
        if inheritance_elem is not None:
            for idx, sub_schema in enumerate(inheritance_elem):
                if not isinstance(sub_schema, openapi.Schema):
                    continue
                yield from get_schema_classes(sub_schema, name + str(idx), module, resolver)

    if schema.type is openapi.Type.object:
        yield get_schema_class(schema, name, module, resolver)

    if enum_class is not None:
        yield enum_class


def get_schema_class(
        schema: openapi.Schema,
        name: str,
        module: ModulePath,
        resolver: ResolverFunc,
) -> Optional[SchemaClass]:
    assert isinstance(schema, openapi.Schema)

    if schema.lapidary_name is not None:
        name = schema.lapidary_name

    logger.debug(name)

    base_type = (
        BuiltinTypeHint.from_str('Exception')
        if schema.lapidary_model_type is openapi.LapidaryModelType.exception
        else TypeHint.from_str('pydantic.BaseModel')
    )
    attributes = get_attributes(schema, name, module, resolver) if schema.properties else []

    return SchemaClass(
        class_name=name,
        base_type=base_type,
        allow_extra=schema.additionalProperties is not False,
        has_aliases=any(['alias' in attr.annotation.field_props for attr in attributes]),
        attributes=attributes,
        docstr=schema.description or None,
        model_type=ModelType[schema.lapidary_model_type.name] if schema.lapidary_model_type else ModelType.model,
    )
