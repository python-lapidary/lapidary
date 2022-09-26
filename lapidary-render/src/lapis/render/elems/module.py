from dataclasses import dataclass

from lapis.render.module_path import ModulePath

template_imports = [
    'builtins',
    'pydantic',
    'typing',
]


@dataclass(frozen=True)
class AbstractModule:
    path: ModulePath
