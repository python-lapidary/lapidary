from dataclasses import dataclass, field

from .client_class import ClientClass, get_client_class
from .module import AbstractModule, template_imports
from .refs import ResolverFunc
from ..module_path import ModulePath
from ...openapi import model as openapi


@dataclass(frozen=True)
class ClientModule(AbstractModule):
    body: ClientClass
    imports: list[str] = field(default_factory=list)


def get_client_class_module(model: openapi.OpenApiModel, client_module: ModulePath, root_module: ModulePath, resolver: ResolverFunc) -> ClientModule:
    client_class = get_client_class(model, root_module, resolver)

    default_imports = [
        'lapis_client_base',
    ]

    response_type_imports = {
        imp
        for func in client_class.methods
        for media_type in func.response_class_map.values()
        for typ in media_type.values()
        for imp in typ.imports()
    }

    type_hint_imports = {
        imp
        for attr in client_class.methods
        for t in attr.params
        for imp in t.annotation.type.imports()
        if imp not in default_imports and imp not in template_imports
    }

    imports = list({*default_imports, *response_type_imports, *type_hint_imports})

    imports.sort()

    return ClientModule(
        path=client_module,
        imports=imports,
        body=client_class,
    )
