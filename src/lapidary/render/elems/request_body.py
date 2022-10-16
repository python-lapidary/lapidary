from typing import Generator, Optional

import inflection
from mimeparse import best_match

from .refs import ResolverFunc
from .schema_class import get_schema_classes
from .schema_class_model import SchemaClass
from .schema_module import _get_schema_module, SchemaModule
from .type_hint import TypeHint, resolve_type_hint
from ..module_path import ModulePath
from ...openapi import model as openapi


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


def get_request_body_module(op: openapi.Operation, module: ModulePath, resolve: ResolverFunc) -> SchemaModule:
    classes = [cls for cls in get_request_body_classes(op, module, resolve)]
    return _get_schema_module(classes, module)


def get_request_body_type(op: openapi.Operation, module: ModulePath, resolve: ResolverFunc) -> Optional[TypeHint]:
    mime_json = best_match(op.requestBody.content.keys(), 'application/json')
    if mime_json == '':
        return None
    schema = op.requestBody.content[mime_json].schema_
    return resolve_type_hint(schema, module, request_type_name(op.operationId), resolve)


def request_type_name(name):
    return inflection.camelize(name) + 'Request'
