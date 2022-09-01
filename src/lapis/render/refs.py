import logging
from typing import Mapping, Any, Callable, TypeVar

from ..openapi import model as openapi

logger = logging.getLogger(__name__)

T = TypeVar('T', openapi.Schema, openapi.Parameter, openapi.SecurityScheme)
ResolverFunc = Callable[[openapi.Reference], tuple[T, list[str]]]


def ref_to_path(ref: openapi.Reference) -> list[str]:
    return ref.ref.split('/')[1:]


def resolve_ref(openapi_model: openapi.OpenApiModel, package: str, ref: openapi.Reference) -> (T, list[str]):
    model: Any = openapi_model
    path = ref_to_path(ref)
    for part in path:
        model = model[part] if isinstance(model, Mapping) else getattr(model, part)

    path = [package, *path]

    logger.debug('%s -> %s', ref.ref, '.'.join(path))
    return model, path
