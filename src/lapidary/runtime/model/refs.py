from __future__ import annotations

import functools
import logging
from typing import Callable, TypeVar, Union, cast, Optional, Any, Tuple, Type, List

from pydantic import BaseModel
from typing_extensions import TypeAlias

from ..json_pointer import decode_json_pointer, encode_json_pointer
from ..module_path import ModulePath
from ..openapi import model as openapi

logger = logging.getLogger(__name__)

T = TypeVar(
    'T',
    openapi.Schema,
    openapi.Parameter,
    openapi.SecurityScheme,
    openapi.Response,
    openapi.Operation,
)
ResolverFunc = Callable[[openapi.Reference, Type[T]], Tuple[T, ModulePath, str]]

SchemaOrRef: TypeAlias = Union[openapi.Schema, openapi.Reference]


def resolve(model: openapi.OpenApiModel, root_package: str, ref: openapi.Reference, type_: type[T] = Any) -> Tuple[T, ModulePath, str]:
    """
    module = {root_package}.{path[0:4]}
    name = path[4:]
    """

    path = ref_to_path(recursive_resolve(model, ref.ref))

    module = ModulePath.from_reference(root_package, recursive_resolve(model, ref.ref), model)
    result = resolve_ref(model, ref.ref, type_)
    if type_ is not Any and not isinstance(result, type_):
        raise TypeError(type(result))

    return result, module, path[-1]


def get_resolver(model: openapi.OpenApiModel, package: str) -> ResolverFunc:
    return cast(ResolverFunc, functools.partial(resolve, model, package))


def _mkref(s: List[str]) -> str:
    return '/'.join(['#', *map(encode_json_pointer, s)])


def ref_to_path(ref: str) -> list[str]:
    return list(map(decode_json_pointer, ref.split('/')[1:]))


def resolve_ref(model: openapi.OpenApiModel, ref: str, t: Optional[type[T]] = Any) -> T:
    result = _schema_get(model, recursive_resolve(model, ref))
    if t is not Any and not isinstance(result, t):
        raise TypeError(ref, t, type(result))
    else:
        return cast(T, result)


def recursive_resolve(model: openapi.OpenApiModel, ref: str) -> str:
    """
    Resolve recursive references
    :return: The last reference, which points to a non-reference object
    """

    stack = [ref]

    while True:
        obj = _schema_get(model, ref)
        if isinstance(obj, openapi.Reference):
            ref = obj.ref
            if ref in stack:
                raise RecursionError(stack, ref)
            else:
                stack.append(ref)
        else:
            return ref


def _schema_get(model: openapi.OpenApiModel, path: str, as_: Type[T] = Any) -> T:
    def resolve_attr_(obj: Any, name: str) -> Any:
        name = decode_json_pointer(name)
        if hasattr(obj, name):
            return getattr(obj, name)
        if hasattr(obj, "__root__") and name in obj.__root__:
            return obj.__root__[name]
        if hasattr(obj, "__contains__") and hasattr(obj, "__getitem__") and name in obj:
            """handle Mapping and DynamicExtendableModel"""
            return obj[name]
        raise KeyError(name)

    def resolve_attr(obj: Any, name: str) -> Any:
        if isinstance(obj, BaseModel) and name in dir(BaseModel):
            return resolve_attr_(obj, name + "_")
        return resolve_attr_(obj, name)

    var = model
    for part in path.split("/")[1:]:
        var = resolve_attr(var, part)

    if as_ is not Any:
        if not isinstance(var, as_):
            raise TypeError(type(var))

    return var
