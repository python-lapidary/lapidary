from __future__ import annotations

import pathlib
from typing import Union, Iterable


class ModulePath:
    _SEP = '.'

    def __init__(self, module: Union[str, list[str]]):
        self.parts = module if isinstance(module, list) else module.split(ModulePath._SEP)

    def str(self):
        return ModulePath._SEP.join(self.parts)

    def to_path(self, root: pathlib.Path):
        return root.joinpath(*self.parts)

    def __truediv__(self, other: Union[str, Iterable[str]]):
        if isinstance(other, str):
            other = [other]
        return ModulePath([*self.parts, *other])

    def __repr__(self):
        return self.str()

    def __eq__(self, other: ModulePath):
        return self.parts == other.parts
