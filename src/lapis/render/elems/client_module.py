from dataclasses import dataclass

from .client_class import ClientClass, get_client_class
from .module import AbstractModule, template_imports
from .refs import ResolverFunc
from ..module_path import ModulePath
from ...openapi import model as openapi


@dataclass(frozen=True, kw_only=True)
class ClientModule(AbstractModule):
    body: ClientClass


def get_client_class_module(model: openapi.OpenApiModel, client_module: ModulePath, root_module: ModulePath, resolver: ResolverFunc) -> ClientModule:
    client_class = get_client_class(model, root_module, resolver)

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

    return ClientModule(
        path=client_module,
        imports=imports,
        type_checking_imports=type_checking_imports,
        body=client_class,
    )
