from lapidary.runtime import openapi
from lapidary.runtime.module_path import ModulePath
from lapidary.runtime.model.refs import ResolverFunc
from .request_body import get_request_body_classes
from .schema_module import SchemaModule, _get_schema_module


def get_request_body_module(op: openapi.Operation, module: ModulePath, resolve: ResolverFunc) -> SchemaModule:
    classes = [cls for cls in get_request_body_classes(op, module, resolve)]
    return _get_schema_module(classes, module)
