from dataclasses import dataclass, field
from typing import Union, Optional

import inflection

from .module import AbstractModule, template_imports
from .param_model_class import get_param_model_classes
from .refs import ResolverFunc
from .schema_class import SchemaClass, get_schema_classes
from ..module_path import ModulePath
from ...openapi import model as openapi


@dataclass(frozen=True)
class SchemaModule(AbstractModule):
    """
    One schema module per schema element directly under #/components/schemas, containing that schema and all non-reference schemas.
    One schema module for all schemas under each operation

    """
    body: list[SchemaClass] = field(default_factory=list)


def get_modules_for_components_schemas(
        schemas: dict[str, Union[openapi.Schema, openapi.Reference]], root_package: ModulePath, resolver: ResolverFunc
) -> list[SchemaModule]:
    result = []
    for name, schema in schemas.items():
        if isinstance(schema, openapi.Schema):
            module = get_module_for_components_schema(schema, root_package / inflection.underscore(name), resolver)
            if module is not None:
                result.append(module)
    return result


def get_module_for_components_schema(schema: openapi.Schema, path: ModulePath, resolver: ResolverFunc) -> Optional[SchemaModule]:
    classes = [cls for cls in get_schema_classes(schema, inflection.camelize(path.parts[-1]), path, resolver)]
    if len(classes):
        return _get_module_for_components_schema(classes, path)


def _get_module_for_components_schema(classes: list[SchemaClass], path: ModulePath) -> SchemaModule:
    imports = list({
        imp
        for cls in classes
        if cls.base_type is not None
        for imp in cls.base_type.imports()
        if imp not in template_imports
    })

    type_checking_imports = list({
        import_
        for schema_class in classes
        for attr in schema_class.attributes
        for import_ in attr.annotation.type.imports()
        if import_ not in imports and import_ not in template_imports and import_ != path.str()
    })
    type_checking_imports.sort()

    return SchemaModule(
        path=path,
        body=classes,
        imports=imports,
        type_checking_imports=type_checking_imports,
    )


def get_module_for_param_model_classes(op: openapi.Operation, module: ModulePath, resolve: ResolverFunc) -> SchemaModule:
    mod = module / 'schemas'
    classes = [cls for cls in get_param_model_classes(op, op.operationId, mod, resolve)]
    return _get_module_for_components_schema(classes, mod)
