from __future__ import annotations

import datetime as dt
import logging
import typing
from typing import Annotated, Union
from uuid import UUID

import inflection
from lapis_client_base.absent import Absent
from pydantic import BaseModel, Field, Extra

from ..openapi import model as openapi

if typing.TYPE_CHECKING:
    from .elems.refs import ResolverFunc, SchemaOrRef
    from .module_path import ModulePath

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


def get_type_ref(schema: openapi.Schema, module: ModulePath, name: str, required: bool, resolver: ResolverFunc) -> TypeRef:
    typ = _get_type_ref(schema, module, name, resolver)

    if schema.nullable:
        typ = typ.union_with(BuiltinTypeRef.from_str('None'))
    if not required:
        typ = typ.union_with(TypeRef.from_type(Absent))

    return typ


def _get_one_of_type_ref(schema: SchemaOrRef, module: ModulePath, name: str, resolve: ResolverFunc) -> TypeRef:
    if len(schema.oneOf) == 1:
        return get_type_ref(schema.oneOf[0], module, name, True, resolve)
    args = []
    for idx, s in enumerate(schema.oneOf):
        if isinstance(s, openapi.Reference):
            s, module, name = resolve(s, openapi.Schema)
        else:
            name = name + str(idx)
        type_ref = get_type_ref(s, module, name, True, resolve)
        args.append(type_ref)

    return GenericTypeRef(
        module='typing',
        name='Union',
        args=args,
    )


def _get_type_ref(schema: openapi.Schema, module: ModulePath, name: str, resolver: ResolverFunc) -> TypeRef:
    if schema.enum:
        return TypeRef(module=module.str(), name=name)
    elif schema.type == openapi.Type.string:
        return TypeRef.from_type(STRING_FORMATS.get(schema.format, str))
    elif schema.type in PRIMITIVE_TYPES:
        return BuiltinTypeRef.from_str(PRIMITIVE_TYPES[schema.type].__name__)
    elif schema.type == openapi.Type.object:
        return _get_type_ref_object(schema, module, name)
    elif schema.type == openapi.Type.array:
        return _get_type_ref_array(schema, module, name, resolver)
    elif schema.anyOf:
        return BuiltinTypeRef.from_str('Unsupported')
    elif schema.oneOf:
        return _get_one_of_type_ref(schema, module, name, resolver)
    elif schema.type is None:
        return TypeRef.from_str('typing.Any')
    else:
        return EllipsisTypeRef()


def _get_type_ref_object(schema: openapi.Schema, module: ModulePath, name: str) -> TypeRef:
    if schema.properties or schema.allOf:
        return TypeRef(module=module.str(), name=name)
    else:
        return TypeRef(module=module.str(), name=name)


def _get_type_ref_array(schema: openapi.Schema, module: ModulePath, parent_name: str, resolver: ResolverFunc) -> TypeRef:
    if isinstance(schema.items, openapi.Reference):
        item_schema, module, name = resolver(schema.items, openapi.Schema)
    else:
        item_schema = schema.items
        name = parent_name + 'Item'

    type_ref = get_type_ref(item_schema, module, name, True, resolver)
    return type_ref.list_of()


class TypeRef(BaseModel):
    module: str
    name: str

    class Config:
        extra = Extra.forbid

    def __repr__(self):
        return self.full_name()

    def full_name(self):
        return self.module + '.' + self.name if self.module != 'builtins' else self.name

    @staticmethod
    def from_str(path: str) -> TypeRef:
        module, name = path.rsplit('.', 1)
        return TypeRef(module=module, name=name)

    @staticmethod
    def from_type(typ: typing.Type) -> TypeRef:
        if hasattr(typ, '__origin__'):
            raise ValueError('Generic types unsupported', typ)
        module = typ.__module__
        name = typ.__name__
        if module == 'builtins':
            return BuiltinTypeRef.from_str(name)
        else:
            return TypeRef(module=module, name=name)

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

    def __eq__(self, other) -> bool:
        return (
                isinstance(other, TypeRef)
                # generic type ref has args, so either both should be generic or none
                and isinstance(self, GenericTypeRef) == isinstance(other, GenericTypeRef)
                and self.module == other.module
                and self.name == other.name
        )

    def __hash__(self) -> int:
        return self.module.__hash__() * 14159 + self.name.__hash__()


class BuiltinTypeRef(TypeRef):
    module: str = 'builtins'

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


class EllipsisTypeRef(TypeRef):
    def full_name(self):
        return '...'

    def type_checking_imports(self) -> list[tuple[str, str]]:
        return []

    def imports(self) -> list[str]:
        return []

    def _types(self) -> list[TypeRef]:
        return []

    def __eq__(self, other) -> bool:
        return isinstance(other, EllipsisTypeRef)

    def __hash__(self) -> int:
        return (2 << 13) - 1


class GenericTypeRef(TypeRef):
    args: Annotated[list[TypeRef], Field(default_factory=list)]

    class Config:
        extra = Extra.forbid

    def union_with(self, other: TypeRef) -> GenericTypeRef:
        if self.module == 'typing' and self.name == 'Union':
            return GenericTypeRef(module=self.module, name=self.name, args=[*self.args, other])
        else:
            return super().union_with(other)

    @staticmethod
    def union_of(types: list[TypeRef]) -> GenericTypeRef:
        args = []
        for typ in types:
            if isinstance(typ, GenericTypeRef) and typ.module == 'typing' and typ.name == 'Union':
                args.append(typ.args)
            else:
                args.append(typ)
        return GenericTypeRef(module='typing', name='Union', args=args)

    def type_checking_imports(self) -> list[tuple[str, str]]:
        return []

    def imports(self) -> list[str]:
        return [
            imp
            for typ in self._types()
            for imp in TypeRef.imports(typ)
            if imp != 'builtins'
        ]

    def _types(self) -> list[TypeRef]:
        return [self, *[typ for arg in self.args for typ in arg._types()]]

    def __repr__(self) -> str:
        return self.full_name()

    def full_name(self) -> str:
        return f'{super().full_name()}[{", ".join(arg.full_name() for arg in self.args)}]'

    def __eq__(self, other) -> bool:
        return (
                isinstance(other, GenericTypeRef)
                and self.module == other.module
                and self.name == other.name
                and self.args == other.args
        )

    def __hash__(self) -> int:
        hash_ = super().__hash__()
        for arg in self.args:
            hash_ = hash_ << 1 + arg.__hash__()
        return hash_


def resolve_type_ref(typ: Union[openapi.Schema, openapi.Reference], module: ModulePath, name: str, resolver: ResolverFunc) -> TypeRef:
    if isinstance(typ, openapi.Reference):
        typ, module, name = resolver(typ, openapi.Schema)
    return get_type_ref(typ, module, name, True, resolver)
