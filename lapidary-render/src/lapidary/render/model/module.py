from dataclasses import dataclass, field

from lapidary.runtime.module_path import ModulePath

template_imports = [
    'builtins',
    'pydantic',
    'typing',
]


@dataclass(frozen=True, kw_only=True)
class AbstractModule:
    path: ModulePath
    imports: list[str] = field(default_factory=list)
