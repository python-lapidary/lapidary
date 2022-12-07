from __future__ import annotations

import functools
import logging
from typing import Callable, TypeVar, Union, Type, cast, Optional, Any, Mapping

import inflection
from typing_extensions import TypeAlias

from ..module_path import ModulePath
from ..openapi import model as openapi

logger = logging.getLogger(__name__)

T = TypeVar('T', openapi.Schema, openapi.Parameter, openapi.SecurityScheme, openapi.Response)
ResolverFunc = Callable[[openapi.Reference, Type[T]], tuple[T, ModulePath, str]]

SchemaOrRef: TypeAlias = Union[openapi.Schema, openapi.Reference]


def resolve(model: openapi.OpenApiModel, root_package: str, ref: openapi.Reference, typ: Type[T]) -> tuple[T, ModulePath, str]:
    """
    module = {root_package}.{path[0:4]}
    name = path[4:]
    """

    path = ref_to_path(recursive_resolve(model, ref.ref))

    if path[0] == 'paths':
        op = resolve_ref(model, _mkref(path[:4]), openapi.Operation)
        if op.operationId:
            path[2:4] = op.operationId

    module = ModulePath(root_package) / path[:-1] / inflection.underscore(path[-1])
    result = resolve_ref(model, _mkref(path), typ)
    assert isinstance(result, typ)
    return result, module, path[-1]


def get_resolver(model: openapi.OpenApiModel, package: str) -> ResolverFunc:
    return cast(ResolverFunc, functools.partial(resolve, model, package))


def _mkref(s: list[str]) -> str:
    return '/'.join(['#', *s])


def ref_to_path(ref: str) -> list[str]:
    return ref.split('/')[1:]


def resolve_ref(model: openapi.OpenApiModel, ref: str, t: Optional[type]) -> Any:
    result = _schema_get(model, recursive_resolve(model, ref))
    if t is not None and not isinstance(result, t):
        raise TypeError(ref, t, type(result))
    else:
        return result


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


def _schema_get(model: openapi.OpenApiModel, ref: str) -> Any:
    path = ref_to_path(ref)
    for part in path:
        model = model[part] if isinstance(model, Mapping) else getattr(model, part)
    return model
