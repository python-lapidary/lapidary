from dataclasses import dataclass, field
from typing import Union, Optional

import inflection

from .module import AbstractModule, template_imports
from .modules import PARAM_MODEL
from .param_model_class import get_param_model_classes
from .refs import ResolverFunc
from .schema_class import SchemaClass, get_schema_classes
from ..module_path import ModulePath
from ...openapi import model as openapi


@dataclass(frozen=True)
class SchemaModule(AbstractModule):
    """
    One schema module per schema element directly under #/components/schemas, containing that schema and all non-reference schemas.
    One schema module for inline request and for response body for each operation
    """
    body: list[SchemaClass] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)


def get_modules_for_components_schemas(
        schemas: dict[str, Union[openapi.Schema, openapi.Reference]], root_package: ModulePath, resolver: ResolverFunc
) -> list[SchemaModule]:
    modules = []
    for name, schema in schemas.items():
        if isinstance(schema, openapi.Schema):
            module = get_schema_module(schema, root_package / inflection.underscore(name), resolver)
            if module is not None:
                modules.append(module)
    return modules


def get_schema_module(schema: openapi.Schema, path: ModulePath, resolver: ResolverFunc) -> Optional[SchemaModule]:
    classes = [cls for cls in get_schema_classes(schema, inflection.camelize(path.parts[-1]), path, resolver)]
    if len(classes) > 0:
        return _get_schema_module(classes, path)


def _get_schema_module(classes: list[SchemaClass], path: ModulePath) -> SchemaModule:
    imports = {
        imp
        for cls in classes
        if cls.base_type is not None
        for imp in cls.base_type.imports()
        if imp not in template_imports
    }

    imports.update({
        import_
        for schema_class in classes
        for attr in schema_class.attributes
        for import_ in attr.annotation.type.imports()
        if import_ not in imports and import_ not in template_imports and import_ != path.str()
    })
    imports = sorted(imports)

    return SchemaModule(
        path=path,
        body=classes,
        imports=imports,
    )


def get_param_model_classes_module(op: openapi.Operation, module: ModulePath, resolve: ResolverFunc) -> SchemaModule:
    mod = module / PARAM_MODEL
    classes = [cls for cls in get_param_model_classes(op, op.operationId, mod, resolve)]
    return _get_schema_module(classes, mod)
