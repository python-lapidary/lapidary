from __future__ import annotations

import functools
import importlib
import itertools
import logging
from collections.abc import Iterable
from dataclasses import dataclass
from typing import List, Tuple, Set, Type, Any, cast

BUILTINS = "builtins"

logger = logging.getLogger(__name__)


@dataclass
class TypeHint:
    module: str
    type_name: str

    def __init__(self, module, type_name):
        self.module = module
        self.type_name = type_name

    def __repr__(self):
        return self.full_name()

    def to_str(self, module: str | None = None) -> str:
        if self.module in (module, "builtins"):
            return self.type_name
        else:
            return self.module + '.' + self.type_name

    def full_name(self) -> str:
        return self.module + ':' + self.type_name

    @staticmethod
    def from_str(path: str) -> TypeHint:
        module, name = path.split(':')
        return TypeHint(module=module, type_name=name)

    def imports(self) -> Iterable[str]:
        return (hint.module for hint in self._types() if hint.module != BUILTINS)

    def _types(self) -> Iterable[TypeHint]:
        return [self]

    def __eq__(self, other) -> bool:
        return (
                isinstance(other, TypeHint)
                # generic type hint has args, so either both should be generic or none
                and isinstance(self, GenericTypeHint) == isinstance(other, GenericTypeHint)
                and self.module == other.module
                and self.type_name == other.type_name
        )

    def __hash__(self) -> int:
        return self.module.__hash__() * 14159 + self.type_name.__hash__()

    def resolve(self) -> Type:
        mod = importlib.import_module(self.module)

        item = mod
        for name in self.type_name.split("."):
            item = getattr(item, name)
        return cast(Type, item)


@dataclass
class GenericTypeHint(TypeHint):
    def __init__(self, module: str, type_name: str, args: Tuple[TypeHint, ...]):
        super().__init__(module, type_name)
        self.args = args

    @staticmethod
    def list_of(type_hint: TypeHint) -> GenericTypeHint:
        return GenericTypeHint(module='typing', type_name='List', args=(type_hint,))

    def _types(self) -> List[TypeHint]:
        return [self, *[typ for arg in self.args for typ in arg._types()]]  # pylint: disable=protected-access

    def resolve(self) -> Type:
        generic = super().resolve()
        return generic[tuple(arg.resolve() for arg in self.args)]

    def full_name(self) -> str:
        return f'{super().full_name()}[{", ".join(arg.full_name() for arg in self.args)}]'

    def str(self, module: str | None = None) -> str:
        return f'{super().to_str(module)}[{", ".join(arg.to_str(module) for arg in self.args)}]'

    @property
    def origin(self) -> TypeHint:
        return TypeHint(module=self.module, type_name=self.type_name)

    def __eq__(self, other) -> bool:
        return (
                isinstance(other, GenericTypeHint)
                and self.module == other.module
                and self.type_name == other.type_name
                and self.args == other.args
        )

    def __hash__(self) -> int:
        hash_ = super().__hash__()
        return functools.reduce(
            lambda x, y: (x << 1) + y,
            itertools.chain((hash_,), (arg.__hash__() for arg in self.args))
        )


class UnionTypeHint(GenericTypeHint):
    def __init__(self, args: tuple[TypeHint, ...]):
        super().__init__(module="typing", type_name="Union", args=args)

    def __eq__(self, other) -> bool:
        return (
                isinstance(other, GenericTypeHint)
                and self.module == other.module
                and self.type_name == other.type_name
                and set(self.args) == set(other.args)
        )

    def __hash__(self) -> int:
        hash_ = super(GenericTypeHint, self).__hash__()
        for arg in self.args:
            hash_ += functools.reduce(
                lambda x, y: x + y,
                (arg.__hash__() for arg in self.args)
            )
        return hash_

    @staticmethod
    def of(*types: TypeHint) -> GenericTypeHint:  # pylint: disable=invalid-name
        args: Set[TypeHint] = set()
        for typ in types:
            if isinstance(typ, GenericTypeHint) and typ.module == 'typing' and typ.type_name == 'Union':
                args.update(typ.args)
            else:
                args.add(typ)
        return UnionTypeHint(args=tuple(args))


def from_type(typ: Any) -> TypeHint:
    if hasattr(typ, '__origin__'):
        raise ValueError('Generic types unsupported', typ)
    module = typ.__module__
    name = getattr(typ, '__name__', None) or typ._name  # type: ignore[attr-defined] # pylint: disable=protected-access
    return TypeHint(module=module, type_name=name)
