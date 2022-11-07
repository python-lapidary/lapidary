from typing import Generator

from mimeparse import best_match

from lapidary.runtime import openapi
from lapidary.runtime.module_path import ModulePath
from lapidary.runtime.model.request_body import request_type_name
from lapidary.runtime.model.refs import ResolverFunc
from .schema_class import get_schema_classes
from .schema_class_model import SchemaClass


def get_request_body_classes(
        operation: openapi.Operation,
        module: ModulePath,
        resolve: ResolverFunc,

) -> Generator[SchemaClass, None, None]:
    rb = operation.requestBody
    if isinstance(rb, openapi.Reference):
        return

    media_map = rb.content
    mime_json = best_match(media_map.keys(), 'application/json')
    schema = media_map[mime_json].schema_
    if isinstance(schema, openapi.Reference):
        return

    yield from get_schema_classes(schema, request_type_name(operation.operationId), module, resolve)


