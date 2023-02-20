from __future__ import annotations

from typing import Any, Iterable


def encode_json_pointer(path: str) -> str:
    return path.replace("~", "~0").replace("/", "~1")


def decode_json_pointer(encoded: str) -> str:
    return encoded.replace("~1", '/').replace("~0", "~")


def _resolve_part(model: Any, part: str) -> Any:
    part_ = decode_json_pointer(part)
    if hasattr(model, '__getitem__') and part_ in model:
        return model[part_]
    if hasattr(model, part_) or hasattr(model, '__getattr__'):
        return getattr(model, part_)
    raise KeyError(part_)


def resolve(model: Any, path: Iterable[str] | str) -> Any:
    parts_ = path.split("/")[1:] if isinstance(path, str) else path
    obj = model
    for part in parts_:
        obj = _resolve_part(obj, part)
    return obj
