# Some encoding methods are missing. Please raise an issue if you need them.

import inspect
import logging
import typing
from collections.abc import Callable, Iterable, Mapping
from enum import Enum, unique
from typing import Optional, Union, cast

from typing_extensions import TypeAlias

from ..pycompat import UNION_TYPES

logger = logging.getLogger(__name__)

Atomic: TypeAlias = Union[str, int, float, bool]
ObjectType: TypeAlias = Mapping[str, Optional[Atomic]]
ValueType: TypeAlias = Union[Atomic, Iterable[Atomic], ObjectType]
Encoder: TypeAlias = Callable[[str, ValueType], Union[str, Iterable[str]]]


@unique
class ParamStyle(Enum):
    matrix = 'matrix'
    label = 'label'
    form = 'form'
    simple = 'simple'
    spaceDelimited = 'spaceDelimited'
    pipeDelimited = 'pipeDelimited'
    deepObject = 'deepObject'


def encode(
    name: str,
    value: Union[Atomic, Mapping[str, Atomic], Iterable[Atomic]],
    typ: type,
    style: ParamStyle,
    explode: bool,
) -> Union[str, Iterable[str]]:
    encoder = get_encode_fn(typ, style, explode)
    assert encoder
    return encoder(name, value)


def get_encode_fn(typ: type, style: ParamStyle, explode: bool) -> Optional[Encoder]:
    origin = typing.get_origin(typ) or typ

    if origin in UNION_TYPES:
        encoders = {subtype: get_encode_fn(subtype, style, explode) for subtype in typing.get_args(typ)}
        encoders = {k: v for k, v in encoders.items() if v is not None}
        if len(encoders) == 1:
            return next(iter(encoders.values()))
        else:
            return encode_union(encoders)  # type: ignore[arg-type]

    if origin is type(None):
        return None
    elif inspect.isclass(origin) and issubclass(origin, (str, int, float, bool)):
        encode_type = 'atomic'
    elif origin == list or (inspect.isclass(origin) and issubclass(origin, Iterable)):
        encode_type = 'array'
    elif origin == dict or (inspect.isclass(origin) and issubclass(origin, Mapping)):
        encode_type = 'object'
    else:
        raise NotImplementedError(typ)

    fn_name = f'encode_{encode_type}_{style.value}{"_explode" if explode else ""}'
    encode_fn = cast(Optional[Encoder], globals().get(fn_name, None))
    if not encode_fn:
        raise TypeError('Unable to encode', typ, style, explode)
    return encode_fn


def encode_union(encoders: Mapping[type, Encoder]) -> Encoder:
    def encode_(name: str, value: ValueType) -> Union[str, Iterable[str]]:
        for formal_typ, encoder in encoders.items():
            if isinstance(value, formal_typ):
                return encoder(name, value)
        else:
            raise TypeError(type(value))

    return encode_


# simple


def encode_atomic_simple(_name: str, value: Atomic) -> str:
    if isinstance(value, bool):
        return 'true' if value else 'false'
    else:
        return str(value)


encode_atomic_simple_explode = encode_atomic_simple


def encode_array_simple(name: str, value: Iterable[Atomic]) -> str:
    return ','.join(encode_atomic_simple(name, item) for item in value)


encode_array_simple_explode = encode_array_simple


def encode_object_simple(_name: str, value: ObjectType) -> str:
    return ','.join(encode_atomic_simple(_name, cast(Atomic, item)) for pair in value.items() for item in pair if pair[1] is not None)


def encode_object_simple_explode(name: str, value: ObjectType) -> str:
    return ','.join(f'{key}={encode_atomic_simple(name, value)}' for key, value in value.items() if value is not None)


# matrix


def encode_atomic_matrix(name: str, value: Atomic) -> str:
    return f';{name}={encode_atomic_simple(name, value)}'


encode_atomic_matrix_explode = encode_atomic_matrix


def encode_array_matrix(name: str, value: Iterable[Atomic]) -> str:
    return f';{name}={",".join(encode_atomic_simple(name, item) for item in value)}'


def encode_array_matrix_explode(name: str, value: Iterable[Atomic]) -> str:
    return ''.join(encode_atomic_matrix_explode(name, item) for item in value)


def encode_object_matrix(name: str, value: Mapping[str, Atomic]) -> str:
    return f';{name}={encode_object_simple(name, value)}'


def encode_object_matrix_explode(name: str, value: Mapping[str, Atomic]) -> str:
    return ''.join(encode_atomic_matrix(key, value) for key, value in value.items())


# form


encode_atomic_form = encode_atomic_simple

encode_atomic_form_explode = encode_atomic_simple

encode_array_form = encode_array_simple


def encode_array_form_explode(name: str, value: Iterable[Atomic]) -> Iterable[str]:
    return [encode_atomic_form(name, item) for item in value]


encode_object_form = encode_object_simple


def encode_object_form_explode(_name: str, value: ObjectType) -> str:
    return '&'.join(encode_atomic_form(key, item) for key, item in value.items() if item)
