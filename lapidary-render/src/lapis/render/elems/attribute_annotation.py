from dataclasses import dataclass
from typing import Optional, Any, Union

from .type_ref import get_type_name, TypeRef
from ..refs import ResolverFunc
from ...openapi import model as openapi

FIELD_PROPS = {
    'multipleOf': 'multiple_of',
    'maximum': 'le',
    'exclusiveMaximum': 'lt',
    'minimum': 'gt',
    'exclusiveMinimum': 'ge',
    'maxLength': 'max_length',
    'minLength': 'min_length',
    'maxItems': 'max_items',
    'minItems': 'min_items',
    'uniqueItems': 'unique_items',
    'maxProperties': 'max_properties',
    'minProperties': 'min_properties',
    'default': 'default',
}


@dataclass(frozen=True)
class AttributeAnnotationModel:
    type: TypeRef
    direction: Optional[str]
    field_props: dict[str, Any]

    style: Optional[str] = None
    explode: Optional[bool] = None
    allowReserved: Optional[bool] = False


def get_attr_annotation(attr_type: Union[openapi.Schema, openapi.Reference], path: list[str], resolver: ResolverFunc) -> AttributeAnnotationModel:
    if isinstance(attr_type, openapi.Reference):
        attr_type, path = resolver(attr_type)

    field_props = {FIELD_PROPS[k]: getattr(attr_type, k) for k in attr_type.__fields_set__ if k in FIELD_PROPS}
    for k, v in field_props.items():
        if isinstance(v, str):
            field_props[k] = f"'{v}'"

    if 'pattern' in attr_type.__fields_set__:
        field_props['regex'] = f"r'${getattr(attr_type, 'pattern')}'"

    if attr_type.readOnly:
        direction = 'lapis_client_base.ParamDirection.read'
    elif attr_type.writeOnly:
        direction = 'lapis_client_base.ParamDirection.write'
    else:
        direction = None

    return AttributeAnnotationModel(
        type=get_type_name(attr_type, path),
        direction=direction,
        field_props=field_props
    )
