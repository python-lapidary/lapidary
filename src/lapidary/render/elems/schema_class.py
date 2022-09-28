import enum
import logging
from dataclasses import dataclass, field
from typing import Optional, Generator

import inflection
from lapidary_base import ABSENT

from .attribute import AttributeModel, get_attributes, get_enum_attribute
from .attribute_annotation import AttributeAnnotationModel
from .refs import ResolverFunc
from ..module_path import ModulePath
from ..type_ref import BuiltinTypeRef, TypeRef
from ...openapi import model as openapi
from ...openapi.model import LapidaryModelType

logger = logging.getLogger(__name__)


class ModelType(enum.Enum):
    model = 'model'
    exception = 'exception'
    enum = 'enum'


@dataclass(frozen=True)
class SchemaClass:
    class_name: str
    base_type: TypeRef

    docstr: Optional[str] = None
    attributes: list[AttributeModel] = field(default_factory=list)
    model_type: ModelType = ModelType.model


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
                yield from get_schema_classes(prop_schema, name + inflection.camelize(prop_name), module, resolver)
    for key in ['oneOf', 'anyOf', 'allOf']:
        inheritance_elem = getattr(schema, key)
        if inheritance_elem is not None:
            for idx, sub_schema in enumerate(inheritance_elem):
                if not isinstance(sub_schema, openapi.Schema):
                    continue
                yield from get_schema_classes(sub_schema, name + str(idx), module, resolver)

    schema_class = get_schema_class(schema, name, module, resolver)
    if schema_class is not None:
        yield schema_class

    if enum_class is not None:
        yield enum_class


def get_schema_class(
        schema: openapi.Schema,
        name: str,
        module: ModulePath,
        resolver: ResolverFunc,
) -> Optional[SchemaClass]:
    if schema.type is not openapi.Type.object:
        return None

    logger.debug(name)

    base_type = TypeRef.from_str('pydantic.BaseModel') if schema.lapidary_model_type is LapidaryModelType.model else BuiltinTypeRef.from_str('Exception')
    attributes = get_attributes(schema, name, module, resolver) if schema.properties else []

    if schema.lapidary_type_name is not None:
        name = schema.lapidary_type_name

    return SchemaClass(
        class_name=name,
        base_type=base_type,
        attributes=attributes,
        docstr=schema.description or None,
        model_type=ModelType[schema.lapidary_model_type.name],
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
        model_type=ModelType.enum,
    )


def get_enum_value(value, schema: openapi.Schema) -> AttributeModel:
    if schema.lapidary_model_type is not ABSENT:
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
