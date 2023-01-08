from __future__ import annotations

import pathlib
from typing import Union, Iterable, List

_SEP = '.'


class ModulePath:
    def __init__(self, module: Union[str, List[str]]):
        if isinstance(module, str):
            module = module.strip()
            if module == "" or module.strip() != module:
                raise ValueError
            parts = module.split(_SEP)
        else:
            parts = module

        if isinstance(parts, list):
            if len(parts) == 0:
                raise ValueError(module)
            self.parts = parts
        else:
            raise ValueError(module)

    def __str__(self):
        return _SEP.join(self.parts)

    def to_path(self, root: pathlib.Path, is_module=True):
        path = root.joinpath(*self.parts)
        if is_module:
            name = self.parts[-1]
            dot_idx = name.rfind('.')
            suffix = name[dot_idx:] if dot_idx != -1 else '.py'
            path = path.with_suffix(suffix)
        return path

    def parent(self) -> ModulePath:
        return ModulePath(self.parts[:-1])

    def __truediv__(self, other: Union[str, Iterable[str]]):
        if isinstance(other, str):
            other = [other]
        return ModulePath([*self.parts, *other])

    def __repr__(self) -> str:
        return f"ModulePath('{self}')"

    def __eq__(self, other: ModulePath):
        return self.parts == other.parts
