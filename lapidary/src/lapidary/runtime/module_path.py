from __future__ import annotations

import pathlib
from typing import Union, Iterable


class ModulePath:
    _SEP = '.'

    def __init__(self, module: Union[str, list[str]]):
        if isinstance(module, str):
            module = module.strip()
            if module == "" or module.strip() != module:
                raise ValueError()
            parts = module.split(ModulePath._SEP)
        else:
            parts = module

        if isinstance(parts, list):
            if len(parts) == 0:
                raise ValueError(module)
            self.parts = parts
        else:
            raise ValueError(module)

    def str(self):
        return ModulePath._SEP.join(self.parts)

    def to_path(self, root: pathlib.Path):
        return root.joinpath(*self.parts).with_suffix('.py')

    def parent(self) -> ModulePath:
        return ModulePath(self.parts[:-1])

    def __truediv__(self, other: Union[str, Iterable[str]]):
        if isinstance(other, str):
            other = [other]
        return ModulePath([*self.parts, *other])

    def __repr__(self):
        return self.str()

    def __eq__(self, other: ModulePath):
        return self.parts == other.parts
