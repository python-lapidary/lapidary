import re
from dataclasses import dataclass
from typing import Any

from .attribute_annotation import AttributeAnnotationModel, get_attr_annotation
from .refs import ResolverFunc, SchemaOrRef
from ..module_path import ModulePath
from ..type_ref import BuiltinTypeRef
from ...openapi import model as openapi

PYTHON_KEYWORDS = [
    'False',
    'None',
    'True',
    'and',
    'as',
    'assert',
    'break',
    'class',
    'continue',
    'def',
    'del',
    'elif',
    'else',
    'except',
    'finally',
    'for',
    'from',
    'global',
    'if',
    'import',
    'in',
    'is',
    'lambda',
    'nonlocal',
    'not',
    'or',
    'pass',
    'raise',
    'return',
    'try',
    'while',
    'with',
    'yield',
]


@dataclass(frozen=True)
class AttributeModel:
    name: str
    annotation: AttributeAnnotationModel
    deprecated: bool = False


def get_attributes(parent_schema: openapi.Schema, parent_class_name: str, module: ModulePath, resolver: ResolverFunc) -> list[AttributeModel]:
    def is_required(schema: openapi.Schema, prop_name: str) -> bool:
        return schema.required is not None and prop_name in schema.required

    return [
        get_attribute(prop_schema, name, parent_class_name, is_required(parent_schema, name), module, resolver)
        for name, prop_schema in parent_schema.properties.items()
    ]


def get_attribute(typ: SchemaOrRef, name: str, parent_name: str, required: bool, module: ModulePath, resolve: ResolverFunc) -> AttributeModel:
    return AttributeModel(
        name=name.replace(':', '_'),
        annotation=get_attr_annotation(typ, name, parent_name, required, module, resolve),
    )


def get_enum_attribute(value: Any) -> AttributeModel:
    name = _name_for_value(value)
    value = "'" + value.replace("'", r"\'") + "'" if value is not None else None
    return AttributeModel(
        name=name,
        annotation=AttributeAnnotationModel(
            type=BuiltinTypeRef.from_type(type(value)),
            field_props={'default': value},
        )
    )


def _name_for_value(value: Any) -> str:
    if value is None: return 'none'
    name = re.compile(r'\W+').sub('_', str(value))
    if name == '' or not name[0].isalpha():
        name = 'v_' + name
    if name in PYTHON_KEYWORDS:
        name += '_'
    return name
