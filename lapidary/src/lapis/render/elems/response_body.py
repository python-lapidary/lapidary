from typing import Generator

import inflection

from .refs import ResolverFunc
from .schema_class import SchemaClass, get_schema_classes
from .schema_module import _get_schema_module, SchemaModule
from ..module_path import ModulePath
from ...openapi import model as openapi


def get_response_body_classes(
        operation: openapi.Operation,
        module: ModulePath,
        resolve: ResolverFunc,

) -> Generator[SchemaClass, None, None]:
    for status_code, response in operation.responses.__root__.items():
        if isinstance(response, openapi.Reference):
            continue
        if response.content is None:
            continue
        for media_type_name, media_type in response.content.items():
            schema = media_type.schema_
            if isinstance(schema, openapi.Reference):
                continue
            yield from get_schema_classes(schema, response_type_name(operation, status_code), module, resolve)


def get_response_body_module(op: openapi.Operation, module: ModulePath, resolve: ResolverFunc) -> SchemaModule:
    classes = [cls for cls in get_response_body_classes(op, module, resolve)]
    return _get_schema_module(classes, module)


def response_type_name(op: openapi.Operation, status_code: str):
    return inflection.camelize(op.operationId) + inflection.camelize(status_code) + 'Response'
