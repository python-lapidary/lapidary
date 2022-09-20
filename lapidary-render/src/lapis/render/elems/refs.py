import functools
import logging
from typing import Callable, TypeVar, Union, Type, cast

import inflection
from typing_extensions import TypeAlias

from ..module_path import ModulePath
from ...openapi import model as openapi

logger = logging.getLogger(__name__)

T = TypeVar('T', openapi.Schema, openapi.Parameter, openapi.SecurityScheme)
ResolverFunc = Callable[[openapi.Reference, Type[T]], tuple[T, ModulePath, str]]

SchemaOrRef: TypeAlias = Union[openapi.Schema, openapi.Reference]


def resolve(model: openapi.OpenApiModel, root_package: str, ref: openapi.Reference, typ: Type[T]) -> tuple[T, ModulePath, str]:
    """
    module = {root_package}.{path[0:4]}
    name = path[4:]
    """

    path = openapi.ref_to_path(model.recursive_resolve(ref.ref))

    if path[0] == 'paths':
        op = model.resolve(_mkref(path[:4]), openapi.Operation)
        if op.operationId:
            path[2:4] = op.operationId

    module = ModulePath(root_package) / path[:-1] / inflection.underscore(path[-1])
    result = model.resolve(_mkref(path), typ)
    assert isinstance(result, typ)
    return result, module, path[-1]


def get_resolver(model: openapi.OpenApiModel, package: str) -> ResolverFunc:
    return cast(ResolverFunc, functools.partial(resolve, model, package))


def _mkref(s: list[str]) -> str:
    return '/'.join(['#', *s])
