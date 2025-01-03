import inspect
import typing
from collections.abc import Iterable, Mapping

import typing_extensions


def make_not_optional(typ: typing.Any) -> typing.Any:
    if typing.get_origin(typ) in (typing.Union, typing_extensions.Union):
        arg_types = typing.get_args(typ)
        non_none_types = tuple(make_not_optional(arg_typ) for arg_typ in arg_types if arg_typ is not type(None))
        if len(non_none_types) == 1:
            return non_none_types[0]
        return typing_extensions.Union[non_none_types]
    else:
        return typ


def is_array_like(typ: typing.Any) -> bool:
    typ = unwrap_origin(typ)
    return inspect.isclass(typ) and issubclass(typ, Iterable) and not (typ in (str, bytes) or issubclass(typ, Mapping))


def unwrap_origin(typ: typing.Any) -> typing.Any:
    return typing.get_origin(typ) or typ
