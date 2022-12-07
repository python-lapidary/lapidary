from typing import Type


def resolve(module: str, name: str) -> Type:
    from importlib import import_module
    mod = import_module(module)
    return getattr(mod, name)
