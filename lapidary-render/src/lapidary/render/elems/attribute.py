import re
from dataclasses import dataclass
from typing import Any, Optional

from .attribute_annotation import AttributeAnnotationModel, get_attr_annotation
from .refs import ResolverFunc, SchemaOrRef
from .type_hint import BuiltinTypeHint
from ..module_path import ModulePath
from ..names import maybe_mangle_name
from ...openapi import model as openapi


@dataclass(frozen=True)
class AttributeModel:
    name: str
    annotation: AttributeAnnotationModel
    deprecated: bool = False
    """Currently not used"""

    required: Optional[bool] = None
    """
    Used for op method params. Required params are rendered before optional, and optional have default value ABSENT
    """


def get_attributes(
        parent_schema: openapi.Schema, parent_class_name: str, module: ModulePath, resolver: ResolverFunc
) -> list[AttributeModel]:
    def is_required(schema: openapi.Schema, prop_name: str) -> bool:
        return schema.required is not None and prop_name in schema.required

    return [
        get_attribute(
            prop_schema,
            parent_schema.lapidary_names.get(name, name),
            name,
            parent_class_name,
            is_required(parent_schema, name),
            module,
            resolver,
        )
        for name, prop_schema in parent_schema.properties.items()
    ]


def get_attribute(
        typ: SchemaOrRef, name: str, alias: str, parent_name: str, required: bool, module: ModulePath,
        resolve: ResolverFunc
) -> AttributeModel:
    if not re.match(r'^[a-zA-Z0-9]\w*$', name, re.ASCII):
        raise ValueError(f'Illegal attribute name "{name}", use x-lapidary-names')
    alias = alias if alias != name else None
    return AttributeModel(
        name=name,
        annotation=get_attr_annotation(typ, name, parent_name, required, module, resolve, alias=alias),
    )


def get_enum_attribute(value: Any, name: str) -> AttributeModel:
    name = maybe_mangle_name(name)
    value = "'" + value.replace("'", r"\'") + "'" if value is not None else None
    return AttributeModel(
        name=name,
        annotation=AttributeAnnotationModel(
            type=BuiltinTypeHint.from_type(type(value)),
            field_props={'default': value},
        )
    )


def _name_for_value(value: Any) -> str:
    if value is None:
        return 'none'
    name = re.compile(r'\W+').sub('_', str(value))
    if name == '' or not name[0].isalpha():
        name = 'v_' + name
    import keyword
    if keyword.iskeyword(name):
        name += '_'
    return name
