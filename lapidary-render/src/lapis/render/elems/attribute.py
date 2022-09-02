import re
from dataclasses import dataclass

from typing import Union, Any

from .attribute_annotation import AttributeAnnotationModel, get_attr_annotation
from .type_ref import BuiltinTypeRef
from ..refs import ResolverFunc
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


def get_attribute(attr_type: Union[openapi.Schema, openapi.Reference], required: bool, path: list[str], resolver: ResolverFunc) -> AttributeModel:
    name = path[-1]
    if isinstance(attr_type, openapi.Reference):
        attr_type, path = resolver(attr_type)

    return AttributeModel(
        name=name,
        annotation=get_attr_annotation(attr_type, required, path, resolver),
        deprecated=attr_type.deprecated,
    )


def get_enum_attribute(value: Any) -> AttributeModel:
    return AttributeModel(
        name=_name_for_value(value),
        annotation=AttributeAnnotationModel(
            type=BuiltinTypeRef.from_type(type(value)),
            field_props={'default': value},
            direction=None,
        )
    )


def _name_for_value(value: Any) -> str:
    result = re.compile(r'\W+').sub('_', str(value))
    if result == '' or not result[0].isalpha():
        result = 'v' + result
    if result in PYTHON_KEYWORDS:
        result += '_'
    return result
