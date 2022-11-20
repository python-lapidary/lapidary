import logging
from dataclasses import dataclass, field

from lapidary.runtime import openapi
from lapidary.runtime.model.client_class import ClientClass, get_client_class
from lapidary.runtime.model.refs import ResolverFunc
from lapidary.runtime.module_path import ModulePath
from .module import AbstractModule, template_imports

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ClientModule(AbstractModule):
    body: ClientClass
    imports: list[str] = field(default_factory=list)


def get_client_class_module(model: openapi.OpenApiModel, client_module: ModulePath, root_module: ModulePath, resolver: ResolverFunc) -> ClientModule:
    client_class = get_client_class(model, root_module, resolver)

    default_imports = [
        'lapidary.runtime',
        'httpx',
    ]

    global_response_type_imports = {
        imp
        for media_type in client_class.init_method.response_map.values()
        for typ in media_type.values()
        for imp in typ.imports()
    }

    response_type_imports = {
        imp
        for func in client_class.methods
        for media_type in func.response_map.values()
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

    imports = list({
        *default_imports,
        *global_response_type_imports,
        *response_type_imports,
        *type_hint_imports,
    })

    imports.sort()

    return ClientModule(
        path=client_module,
        imports=imports,
        body=client_class,
    )
