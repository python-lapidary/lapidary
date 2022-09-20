from dataclasses import dataclass

from lapis.render.module_path import ModulePath

template_imports = ['typing', 'builtins']


@dataclass(frozen=True)
class AbstractModule:
    path: ModulePath
