from __future__ import annotations

import datetime as dt
from typing import Iterable, Union, List
from uuid import UUID

from .refs import ResolverFunc
from .type_hint import GenericTypeHint, from_type, TypeHint, UnionTypeHint
from .. import openapi, Absent
from ..module_path import ModulePath

STRING_FORMATS = {
    'uuid': UUID,
    'date': dt.date,
    'date-time': dt.datetime,
}

PRIMITIVE_TYPES = {
    openapi.Type.string: from_type(str),
    openapi.Type.integer: from_type(int),
    openapi.Type.number: from_type(float),
    openapi.Type.boolean: from_type(bool),
}


def get_type_hint(
        schema: openapi.Schema, module: ModulePath, name: str, required: bool, resolver: ResolverFunc
) -> TypeHint:
    typ = _get_type_hint(schema, module, name, resolver)

    if schema.nullable:
        typ = UnionTypeHint.of(typ, from_type(type(None)))
    if not required:
        typ = UnionTypeHint.of(typ, from_type(Absent))

    return typ


def _get_one_of_type_hint(
        component_schemas: Iterable[Union[openapi.Schema, openapi.Reference]], module: ModulePath, name: str, resolve: ResolverFunc
) -> TypeHint:
    args = []
    for idx, sub_schema in enumerate(component_schemas):
        if isinstance(sub_schema, openapi.Reference):
            sub_schema_, sub_module, sub_name = resolve(sub_schema, openapi.Schema)
        else:
            sub_name = name + str(idx)
            sub_module = module
            sub_schema_ = sub_schema

        if sub_schema_.lapidary_name is not None:
            sub_name = sub_schema_.lapidary_name

        type_hint = get_type_hint(sub_schema_, sub_module, sub_name, True, resolve)
        args.append(type_hint)

    return GenericTypeHint(
        module='typing',
        type_name='Union',
        args=tuple(args),
    )


def _get_composite_type_hint(
        component_schemas: List[Union[openapi.Schema, openapi.Reference]], module: ModulePath, name: str, resolve: ResolverFunc
) -> TypeHint:
    if len(component_schemas) != 1:
        raise NotImplementedError(name, 'Multiple component schemas (allOf, anyOf, oneOf) are currently unsupported.')

    return resolve_type_hint(component_schemas[0], module, name, resolve)


def _get_type_hint(schema: openapi.Schema, module: ModulePath, name: str, resolver: ResolverFunc) -> TypeHint:  # pylint: disable=too-many-return-statements
    class_name = name.replace(' ', '_')
    if schema.enum:
        return TypeHint(module=str(module), type_name=class_name)
    elif schema.type == openapi.Type.string:
        return from_type(STRING_FORMATS.get(schema.format, str) if schema.format else str)
    elif schema.type in PRIMITIVE_TYPES:
        return PRIMITIVE_TYPES[schema.type]
    elif schema.type == openapi.Type.object:
        return _get_type_hint_object(schema, module, class_name)
    elif schema.type == openapi.Type.array:
        return _get_type_hint_array(schema, module, class_name, resolver)
    elif schema.anyOf:
        return _get_composite_type_hint(schema.anyOf, module, class_name, resolver)
    elif schema.oneOf:
        return _get_one_of_type_hint(schema.oneOf, module, class_name, resolver)
    elif schema.allOf:
        return _get_composite_type_hint(schema.allOf, module, class_name, resolver)
    elif schema.type is None:
        return TypeHint.from_str('typing:Any')
    else:
        raise NotImplementedError


def _get_type_hint_object(_: openapi.Schema, module: ModulePath, name: str) -> TypeHint:
    return TypeHint(module=str(module), type_name=name)


def _get_type_hint_array(schema: openapi.Schema, module: ModulePath, parent_name: str,
                         resolver: ResolverFunc) -> TypeHint:
    if isinstance(schema.items, openapi.Reference):
        item_schema, module, name = resolver(schema.items, openapi.Schema)
    else:
        item_schema = schema.items
        name = parent_name + 'Item'

    type_hint = get_type_hint(item_schema, module, name, True, resolver)
    return GenericTypeHint.list_of(type_hint)


def resolve_type_hint(
        schema: Union[openapi.Schema, openapi.Reference], module: ModulePath, name: str, resolver: ResolverFunc
) -> TypeHint:
    if isinstance(schema, openapi.Reference):
        schema_, module, name = resolver(schema, openapi.Schema)
    else:
        schema_ = schema
    return get_type_hint(schema_, module, name, True, resolver)
