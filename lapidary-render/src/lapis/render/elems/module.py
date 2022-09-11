from dataclasses import dataclass, field

from typing import TypeVar, TypeAlias

from lapis.render.module_path import ModulePath

T = TypeVar('T')

SchemaImport: TypeAlias = tuple[str, str]

template_imports = ['typing', 'builtins']


@dataclass(frozen=True, kw_only=True)
class AbstractModule:
    path: ModulePath
    imports: list[str] = field(default_factory=list)
    type_checking_imports: list[SchemaImport] = field(default_factory=list)
