from dataclasses import dataclass
from typing import Union, Any

from .attribute_annotation import AttributeAnnotationModel, get_attr_annotation
from .type_ref import BuiltinTypeRef
from ..refs import ResolverFunc
from ...openapi import model as openapi


@dataclass(frozen=True)
class AttributeModel:
    name: str
    annotation: AttributeAnnotationModel
    deprecated: bool = False


def get_attribute(attr_type: Union[openapi.Schema, openapi.Reference], required: bool, path: list[str], resolver: ResolverFunc) -> AttributeModel:
    name = path[-1]
    if isinstance(attr_type, openapi.Reference):
        attr_type, path = resolver(attr_type)

    return AttributeModel(
        name=name,
        annotation=get_attr_annotation(attr_type, required, path, resolver),
        deprecated=attr_type.deprecated,
    )


def get_enum_attribute(name: str, value: Any) -> AttributeModel:
    return AttributeModel(
        name=name,
        annotation=AttributeAnnotationModel(
            type=BuiltinTypeRef.from_type(type(value)),
            field_props={'default': value},
            direction=None,
        )
    )
