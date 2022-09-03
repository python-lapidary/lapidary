from dataclasses import dataclass
from typing import TypeVar, TypeAlias

import inflection

from .client_class import get_client_class
from .schema_class import get_schema_class
from ..refs import ResolverFunc
from ...openapi import model as openapi

T = TypeVar('T')

SchemaImport: TypeAlias = tuple[str, str]


@dataclass(frozen=True)
class Module:
    name: str
    package: str
    imports: list[str]
    body: T
    type_checking_imports: list[SchemaImport]


def get_schema_class_module(model: openapi.Schema, path: list[str], resolver: ResolverFunc) -> Module:
    schema_class = get_schema_class(model, path, resolver)

    type_checking_imports = {t for attr in schema_class.attributes for t in attr.annotation.type.type_checking_imports()}
    imports = {t for attr in schema_class.attributes for t in attr.annotation.type.imports()}
    imports.update(schema_class.base_type.imports())

    return Module(
        package='.'.join(path[:-1]),
        name=inflection.underscore(schema_class.class_name),
        body=schema_class,
        imports=list({
            'typing',
            'lapis_client_base',
            *imports,
        }),
        type_checking_imports=list(type_checking_imports),
    )


def get_client_class_module(model: openapi.OpenApiModel, package_name: str, resolver: ResolverFunc) -> Module:
    client_class = get_client_class(model, package_name, resolver)

    imports = list({
        imp
        for attr in client_class.methods
        for t in attr.params
        for imp in t.annotation.type.imports()
    })

    import_list = [
        'typing',
        'pydantic',
        'deprecation',
        'lapis_client_base',
        *imports,
    ]
    import_list.sort()

    return Module(
        package=package_name,
        name='client',
        body=client_class,
        imports=import_list,
        type_checking_imports=[],
    )
