from dataclasses import dataclass
from typing import Union

from .attribute_annotation import AttributeAnnotationModel, get_attr_annotation
from ..refs import ResolverFunc
from ...openapi import model as openapi


@dataclass(frozen=True)
class AttributeModel:
    name: str
    type: AttributeAnnotationModel
    deprecated: bool = False


def get_attribute(attr_type: Union[openapi.Schema, openapi.Reference], required: bool, path: list[str], resolver: ResolverFunc) -> AttributeModel:
    name = path[-1]
    if isinstance(attr_type, openapi.Reference):
        attr_type, path = resolver(attr_type)

    return AttributeModel(
        name=name,
        type=get_attr_annotation(attr_type, required, path, resolver),
        deprecated=attr_type.deprecated,
    )
