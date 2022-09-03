from dataclasses import dataclass
from typing import TypeVar, TypeAlias

import inflection

from .client_class import get_client_class
from .schema_class import get_schema_class
from ..refs import ResolverFunc
from ...openapi import model as openapi

T = TypeVar('T')

SchemaImport: TypeAlias = tuple[str, str]

template_imports = ['typing']


@dataclass(frozen=True)
class Module:
    name: str
    package: str
    imports: list[str]
    body: T
    type_checking_imports: list[SchemaImport]


def get_schema_class_module(model: openapi.Schema, path: list[str], resolver: ResolverFunc) -> Module:
    schema_class = get_schema_class(model, path, resolver)

    imports = schema_class.base_type.imports()
    imports.sort()

    type_checking_imports = list({
        t
        for attr in schema_class.attributes
        for t in attr.annotation.type.imports()
        if t not in imports and t not in template_imports
    })
    template_imports.sort()

    return Module(
        package='.'.join(path[:-1]),
        name=inflection.underscore(schema_class.class_name),
        body=schema_class,
        imports=imports,
        type_checking_imports=type_checking_imports,
    )


def get_client_class_module(model: openapi.OpenApiModel, package_name: str, resolver: ResolverFunc) -> Module:
    client_class = get_client_class(model, package_name, resolver)

    imports = [
        'lapis_client_base',
    ]

    type_checking_imports = list({
        imp
        for attr in client_class.methods
        for t in attr.params
        for imp in t.annotation.type.imports()
        if imp not in imports and imp not in template_imports
    })
    type_checking_imports.sort()

    return Module(
        package=package_name,
        name='client',
        body=client_class,
        imports=imports,
        type_checking_imports=type_checking_imports,
    )
