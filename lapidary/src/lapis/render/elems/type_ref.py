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


def get_type_ref(schema: openapi.Schema, required: bool, path: list[str], resolver: ResolverFunc) -> TypeRef:
    typ = _get_type_ref(schema, path, resolver)

    if schema.nullable:
        typ = typ.union_with(BuiltinTypeRef.from_str('None'))
    if not required or schema.readOnly or schema.writeOnly:
        typ = typ.union_with(TypeRef.from_type(Absent))

    return typ


def _get_type_ref(schema: openapi.Schema, path: list[str], resolver: ResolverFunc) -> TypeRef:
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
            return _get_type_ref_from_path(path, True)
    elif schema.type in PRIMITIVE_TYPES:
        return BuiltinTypeRef.from_str(PRIMITIVE_TYPES[schema.type].__name__)
    elif schema.type == openapi.Type.array:
        if isinstance(schema.items, openapi.Reference):
            item_schema, path = resolver(schema.items)
        else:
            item_schema = schema.items
            path = [*path, inflection.camelize(path[-1]) + 'Item']
        type_ref = get_type_ref(item_schema, True, path, resolver)
        return type_ref.list_of()
    return TypeRef.from_type(Any)


def _get_type_ref_from_path(path: list[str], schema_type: bool) -> TypeRef:
    module = '.'.join(path[:-1])
    name = inflection.camelize(path[-1])
    return TypeRef(module=module, name=name, schema_type=schema_type)


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
            return self.full_name()

    def full_name(self):
        return self.module + '.' + self.name

    @staticmethod
    def from_str(path: str, schema_type: bool = False) -> TypeRef:
        module, name = path.rsplit('.', 1)
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
        return []

    def imports(self) -> list[str]:
        return [self.module]

    def union_with(self, other: TypeRef) -> GenericTypeRef:
        return GenericTypeRef(module='typing', name='Union', args=[self, other])

    def list_of(self) -> GenericTypeRef:
        return GenericTypeRef(module='builtins', name='list', args=[self])

    def _types(self) -> list[TypeRef]:
        return [self]


class BuiltinTypeRef(TypeRef):
    module: str = 'builtins'
    schema_type = False

    class Config:
        extra = Extra.forbid

    def __repr__(self):
        return self.full_name()

    @staticmethod
    def from_str(name: str) -> BuiltinTypeRef:
        return BuiltinTypeRef(name=name)

    def imports(self) -> list[str]:
        return []

    def full_name(self):
        return self.name


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
        return []

    def imports(self) -> list[str]:
        return [imp for typ in self._types() for imp in TypeRef.imports(typ)]

    def _types(self) -> list[TypeRef]:
        return [self, *[typ for arg in self.args for typ in arg._types()]]

    def __repr__(self) -> str:
        return self.full_name()

    def full_name(self) -> str:
        return f'{super().full_name()}[{", ".join(arg.full_name() for arg in self.args)}]'
