from __future__ import annotations

import datetime as dt
import logging
import typing
from typing import Annotated, Any
from uuid import UUID

import inflection
from pydantic import BaseModel, Field, Extra

from ...openapi import model as openapi

logger = logging.getLogger(__name__)

STRING_FORMATS = {
    'uuid': UUID,
    'date': dt.date,
    'date-time': dt.datetime,
}

PRIMITIVE_TYPES = {
    openapi.Type.string: str,
    openapi.Type.integer: int,
    openapi.Type.number: float,
    openapi.Type.boolean: bool,
}


def module_name(path: list[str]) -> str:
    return '.'.join([*path[:-1], inflection.underscore(path[-1])])


def get_type_name(schema: openapi.Schema, path: list[str]) -> TypeRef:
    name = schema.type.name if schema.type is not None else None
    logger.debug('%s %s', name, '.'.join(path))

    if schema.enum:
        return TypeRef(module=module_name(path), name=inflection.camelize(path[-1]), schema_type=True)
    elif schema.type == openapi.Type.string:
        return TypeRef.from_type(STRING_FORMATS.get(schema.format, str))
    elif schema.type == openapi.Type.object:
        if schema.properties or schema.allOf:
            return TypeRef(module=module_name(path), name=inflection.camelize(path[-1]), schema_type=True)
        elif schema.anyOf:
            return BuiltinTypeRef.from_str('Unsupported')
        elif schema.oneOf:
            return BuiltinTypeRef.from_str('Unsupported')
        else:
            return TypeRef.from_type(Any)
    elif schema.type in PRIMITIVE_TYPES:
        return BuiltinTypeRef.from_str(PRIMITIVE_TYPES[schema.type].__name__)
    return TypeRef.from_type(Any)


class TypeRef(BaseModel):
    module: str
    name: str
    schema_type: bool

    class Config:
        extra = Extra.forbid

    def __repr__(self):
        if self.schema_type:
            return self.name
        else:
            return self.module + '.' + self.name

    @staticmethod
    def from_str(path: str, schema_type: bool = False) -> TypeRef:
        module, name = path.rsplit(path, 1)
        return TypeRef(module=module, name=name, schema_type=schema_type)

    @staticmethod
    def from_type(typ: typing.Type) -> TypeRef:
        if hasattr(typ, '__origin__'):
            raise ValueError('Generic types unsupported', typ)
        module = typ.__module__
        name = typ.__name__
        if module == 'builtins':
            return BuiltinTypeRef.from_str(name)
        else:
            return TypeRef(module=module, name=name, schema_type=False)

    def type_checking_imports(self) -> list[tuple[str, str]]:
        return [(self.module, self.name)] if self.schema_type else []

    def imports(self) -> list[str]:
        return [self.module] if not self.schema_type else []


class BuiltinTypeRef(TypeRef):
    module: str = 'builtins'
    schema_type = False

    class Config:
        extra = Extra.forbid

    def __repr__(self):
        return self.name

    @staticmethod
    def from_str(name: str) -> BuiltinTypeRef:
        return BuiltinTypeRef(name=name)


class GenericTypeRef(TypeRef):
    schema_type = False
    args: Annotated[list[TypeRef], Field(default_factory=list)]

    class Config:
        extra = Extra.forbid

    def __repr__(self):
        module_dot = '' if self.schema_type else self.module + '.'
        return f'{module_dot}{self.name}[{",".join(self.args.__repr__())}]'
