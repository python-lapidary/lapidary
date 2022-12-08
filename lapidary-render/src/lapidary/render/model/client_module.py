import logging
from dataclasses import dataclass, field

from lapidary.runtime import openapi
from lapidary.runtime.model import ResolverFunc
from lapidary.runtime.module_path import ModulePath

from .client_class import ClientClass, get_client_class
from .module import AbstractModule, template_imports

logger = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class ClientModule(AbstractModule):
    body: ClientClass = field()


def get_client_class_module(model: openapi.OpenApiModel, client_module: ModulePath, root_module: ModulePath, resolver: ResolverFunc) -> ClientModule:
    client_class = get_client_class(model, root_module, resolver)

    default_imports = [
        'lapidary.runtime',
        'httpx',
    ]

    global_response_type_imports = {
        import_
        for type_hint in client_class.init_method.response_types
        for import_ in type_hint.imports()
    }

    response_type_imports = {
        import_
        for func in client_class.methods
        if func.response_type is not None
        for import_ in func.response_type.imports()
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
