from __future__ import annotations

import pathlib
from itertools import chain
from typing import Union, Iterable, Sequence, Any, Iterator

from . import openapi
from .json_pointer import decode_json_pointer, resolve
from .names import escape_name

_SEP = '.'


class ModulePath:
    def __init__(self, module: Union[str, Sequence[str]]):
        if isinstance(module, str):
            module = module.strip()
            if module == "" or module.strip() != module:
                raise ValueError
            parts = module.split(_SEP)
        else:
            parts = module

        if isinstance(parts, Sequence):
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

    def __eq__(self, other: Any) -> bool:
        return hasattr(other, 'parts') and self.parts == other.parts

    @staticmethod
    def from_reference(root: ModulePath | str, reference: str, model: openapi.OpenApiModel) -> ModulePath:
        parts = list(map(decode_json_pointer, reference.split('/')))
        if parts[0] != "#":
            raise ValueError(reference)

        module_parts = list(chain((str(root),), _to_module_parts(parts, model)))

        return ModulePath(module_parts)


def _to_module_parts(parts: Sequence[str], model: openapi.OpenApiModel) -> Iterator[str]:
    parts_len = len(parts)
    if parts_len < 2:
        return

    if parts[1] == 'paths' and parts_len > 3:
        yield "ops"
        op: openapi.Operation = resolve(model, parts[1:4])
        yield op.operationId

        if parts_len < 5:
            return

        yield parts[4]

        if parts[4] != "parameters":
            yield from map(escape_name, parts[5:-1])
        else:
            yield parts[4]

    else:
        for part in parts[1:]:
            yield escape_name(part)
