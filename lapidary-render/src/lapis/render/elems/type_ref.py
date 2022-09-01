from __future__ import annotations

import datetime as dt
import logging
import typing
from typing import Annotated, Any
from uuid import UUID

import inflection
from lapis_client_base import Absent
from pydantic import BaseModel, Field, Extra

from ..refs import ResolverFunc
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


def get_type_name(schema: openapi.Schema, required: bool, path: list[str], resolver: ResolverFunc) -> TypeRef:
    typ = _get_type_name(schema, path, resolver)

    if schema.nullable:
        typ = typ.union_with(BuiltinTypeRef.from_str('None'))
    if not required or schema.readOnly or schema.writeOnly:
        typ = typ.union_with(TypeRef.from_type(Absent))

    return typ


def _get_type_name(schema: openapi.Schema, path: list[str], resolver: ResolverFunc) -> TypeRef:
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
    elif schema.type == openapi.Type.array:
        if isinstance(schema.items, openapi.Reference):
            item_schema, path = resolver(schema.items)
        else:
            item_schema = schema.items
            path = [*path, inflection.camelize(path[-1]) + 'Item']
        type_ref = get_type_name(item_schema, True, path, resolver)
        return type_ref.list_of()
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

    def union_with(self, other: TypeRef) -> GenericTypeRef:
        return GenericTypeRef(module='typing', name='Union', args=[self, other])

    def list_of(self) -> GenericTypeRef:
        return GenericTypeRef(module='builtins', name='list', args=[self])


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

    def union_with(self, other: TypeRef) -> GenericTypeRef:
        if self.module == 'typing' and self.name == 'Union':
            return GenericTypeRef(module=self.module, name=self.name, args=[*self.args, other])
        else:
            return super().union_with(other)

    def type_checking_imports(self) -> list[tuple[str, str]]:
        result = super().type_checking_imports()
        result += [(arg.module, arg.name) for arg in self.args if arg.schema_type]
        return result

    def imports(self) -> list[str]:
        result = super().imports()
        result += [arg.module for arg in self.args if not arg.schema_type]
        return result

    def __repr__(self):
        module_dot = '' if self.schema_type else self.module + '.'
        return f'{module_dot}{self.name}[{",".join(self.args.__repr__())}]'
