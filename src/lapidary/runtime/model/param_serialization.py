"""Converting between types returned by pydantic and accepted by httpx"""

# Some encoding methods are missing. Please raise an issue if you need them.
import abc
import datetime as dt
import itertools
import uuid
from collections.abc import Iterable, Mapping
from decimal import Decimal

import typing_extensions as typing

from ..metattype import make_not_optional, unwrap_origin

# Some basic scalar types that we're sure are passed unchanged by pydantic
PYTHON_SCALARS = (
    bool,
    float,
    int,
    str,
)

# Some basic scalar types that we're sure are handled by pydantic
SCALAR_TYPES = (
    *PYTHON_SCALARS,
    Decimal,
    dt.date,
    dt.datetime,
    dt.time,
    uuid.UUID,
)

ScalarType: typing.TypeAlias = typing.Union[PYTHON_SCALARS]  # type: ignore[valid-type]
ArrayType: typing.TypeAlias = typing.Iterable[ScalarType]
ObjectType: typing.TypeAlias = typing.Mapping[str, typing.Optional[ScalarType]]
ValueType: typing.TypeAlias = typing.Union[str, ArrayType, ObjectType]
Entry: typing.TypeAlias = tuple[str, ScalarType]
Multimap: typing.TypeAlias = Iterable[Entry]


class SerializationError(ValueError):
    pass


class StringSerializationStyle(abc.ABC):
    """Used for serializing path parameters"""

    @classmethod
    def serialize(cls, name: str, value: ValueType) -> str:
        if isinstance(value, PYTHON_SCALARS):
            return cls.serialize_scalar(name, value)
        elif isinstance(value, Mapping):
            return cls.serialize_object(name, value)
        elif isinstance(value, Iterable):
            return cls.serialize_array(name, value)
        else:
            raise SerializationError(type(value))

    @classmethod
    @abc.abstractmethod
    def serialize_object(cls, name: str, value: ObjectType) -> str:
        pass

    @classmethod
    @abc.abstractmethod
    def serialize_array(cls, name: str, value: ArrayType) -> str:
        pass

    @classmethod
    @abc.abstractmethod
    def serialize_scalar(cls, name: str, value: ScalarType) -> str:
        pass


class MultimapSerializationStyle(abc.ABC):
    @classmethod
    def serialize(cls, name: str, value: ValueType) -> Multimap:
        if value is None:
            return ()
        elif isinstance(value, PYTHON_SCALARS):
            return cls.serialize_scalar(name, value)
        elif isinstance(value, Mapping):
            return cls.serialize_object(name, value)
        elif isinstance(value, Iterable):
            return cls.serialize_array(name, value)
        else:
            raise SerializationError(type(value))

    @classmethod
    @abc.abstractmethod
    def serialize_object(cls, name: str, value: ObjectType) -> Multimap:
        pass

    @classmethod
    @abc.abstractmethod
    def serialize_array(cls, name: str, value: ArrayType) -> Multimap:
        pass

    @classmethod
    @abc.abstractmethod
    def serialize_scalar(cls, name: str, value: ScalarType) -> Multimap:
        pass

    @classmethod
    def deserialize(cls, value: typing.Any, target: type) -> ValueType:
        target = unwrap_origin(make_not_optional(target))
        if target in PYTHON_SCALARS:
            return cls.deserialize_scalar(value, target)
        elif issubclass(target, Mapping):
            return cls.deserialize_object(value, target)
        elif issubclass(target, Iterable):
            return cls.deserialize_array(value, target)
        else:
            raise SerializationError(type(value), target)

    @classmethod
    def deserialize_scalar(cls, value: str, _) -> ScalarType:
        # leave handling to pydantic
        return value

    @classmethod
    @abc.abstractmethod
    def deserialize_object(cls, value: str, _) -> ValueType:
        pass

    @classmethod
    @abc.abstractmethod
    def deserialize_array(cls, value: str, _) -> ArrayType:
        pass


class SimpleMultimap(MultimapSerializationStyle):
    @classmethod
    def serialize_object(cls, name: str, value: ObjectType) -> Multimap:
        return [(name, ','.join(itertools.chain.from_iterable(cls._scalar_as_entry(k, v) for k, v in value.items())))]

    @classmethod
    def serialize_array(cls, name: str, value: ArrayType) -> Multimap:
        return [(name, ','.join(cls._serialize_scalar(scalar) for scalar in value))]

    @classmethod
    def serialize_scalar(cls, name: str, value: ScalarType) -> Multimap:
        return [cls._scalar_as_entry(name, value)] if value else ()

    @staticmethod
    def _serialize_scalar(value: ScalarType) -> str:
        return str(value)

    @classmethod
    def _scalar_as_entry(cls, name: str, value: ScalarType) -> Entry:
        return name, cls._serialize_scalar(value)

    @classmethod
    def deserialize_object(cls, value: str, _) -> ValueType:
        tokens = value.split(',')
        return dict((k, cls.deserialize_scalar(v, None)) for k, v in zip(tokens[::2], tokens[1::2]))

    @classmethod
    def deserialize_array(cls, value: str, _) -> ArrayType:
        return [cls.deserialize_scalar(scalar, None) for scalar in value.split(',')]


class SimpleString(StringSerializationStyle):
    @classmethod
    def serialize_object(cls, name: str, value: ObjectType) -> str:
        return ','.join(entry for name, entry in SimpleMultimap.serialize_object(name, value))

    @classmethod
    def serialize_array(cls, name: str, value: ArrayType) -> str:
        return ','.join(entry for name, entry in SimpleMultimap.serialize_array(name, value))

    @classmethod
    def serialize_scalar(cls, name: str, value: ScalarType) -> str:
        return SimpleMultimap._serialize_scalar(value)


# form


class FormExplode(MultimapSerializationStyle):
    @classmethod
    def serialize_scalar(cls, name: str, value: ScalarType) -> Multimap:
        return SimpleMultimap.serialize_scalar(name, value)

    @classmethod
    def serialize_array(cls, name: str, value: ArrayType) -> Multimap:
        return itertools.chain.from_iterable(cls.serialize_scalar(name, item) for item in value)

    @classmethod
    def serialize_object(cls, _name: str, value: ObjectType) -> Multimap:
        """Disregard name, return a map of {key: value}"""
        return itertools.chain.from_iterable(cls.serialize_scalar(key, item) for key, item in value.items() if item)

    @classmethod
    def deserialize_array(cls, value: str, _) -> ArrayType:
        raise NotImplementedError


Form = SimpleMultimap
