"""Converting between python values and HTTP messages"""

# Some encoding methods are missing. Please raise an issue if you need them.
import abc
import datetime as dt
import itertools
import uuid
from collections.abc import Iterable, Mapping
from decimal import Decimal

import typing_extensions as typing

from ..metattype import make_not_optional

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


class SerializationError(ValueError):
    pass


class SerializationStyle(abc.ABC):
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

    @classmethod
    def deserialize(cls, value: typing.Any, target: type) -> ValueType:
        target = make_not_optional(target)
        if target in PYTHON_SCALARS:
            return cls.deserialize_scalar(value)
        elif issubclass(target, Mapping):
            return cls.deserialize_object(value)
        elif issubclass(target, Iterable):
            return cls.deserialize_array(value)
        else:
            raise SerializationError(type(value), target)

    @classmethod
    @abc.abstractmethod
    def deserialize_scalar(cls, value: str) -> str:
        pass

    @classmethod
    @abc.abstractmethod
    def deserialize_object(cls, value: str) -> ValueType:
        pass

    @classmethod
    @abc.abstractmethod
    def deserialize_array(cls, value: str) -> ArrayType:
        pass


class Simple(SerializationStyle):
    @classmethod
    def serialize_object(cls, name: str, value: ObjectType) -> str:
        return ','.join(itertools.chain(*[(cls.serialize_scalar(k, v)) for k, v in value.items() if v is not None]))

    @classmethod
    def serialize_array(cls, name: str, value: ArrayType) -> str:
        return ','.join(cls.serialize_scalar(name, scalar) for scalar in value)

    @staticmethod
    def serialize_scalar(name: str, value: ScalarType) -> str:
        return str(value)

    @classmethod
    def deserialize(cls, value: typing.Any, target: type) -> ValueType:
        target = make_not_optional(target)
        if target in PYTHON_SCALARS:
            return cls.deserialize_scalar(value)
        elif issubclass(target, Mapping):
            return cls.deserialize_object(value)
        elif issubclass(target, Iterable):
            return cls.deserialize_array(value)
        else:
            raise SerializationError(type(value), target)

    @classmethod
    def deserialize_scalar(cls, value: str) -> str:
        return value

    @classmethod
    def deserialize_object(cls, value: str) -> ValueType:
        tokens = value.split(',')
        return dict((k, cls.deserialize_scalar(v)) for k, v in zip(tokens[::2], tokens[1::2]))

    @classmethod
    def deserialize_array(cls, value: str) -> ArrayType:
        return [cls.deserialize_scalar(scalar) for scalar in value.split(',')]


class BaseNamedSerializer(SerializationStyle):
    @classmethod
    def serialize_scalar(cls, name: str, value: ScalarType) -> str:
        return f'{name}={super().serialize_scalar(name, value)}'

    @classmethod
    def serialize_object(cls, name: str, value: ObjectType) -> str:
        return (
            name
            + '='
            + (','.join(itertools.chain(*[cls.serialize_scalar(name, item) for name, item in value.items() if item is not None])))
        )

    @classmethod
    def serialize_array(cls, name: str, value: ArrayType) -> str:
        return name + '=' + (','.join(value))

    @staticmethod
    def deserialize_scalar(value: str) -> str:
        raise NotImplementedError

    @staticmethod
    def deserialize_object(value: str) -> ObjectType:
        raise NotImplementedError

    @staticmethod
    def deserialize_array(value: str) -> ArrayType:
        raise NotImplementedError


# matrix


class Matrix(BaseNamedSerializer):
    @classmethod
    def serialize_scalar(cls, name: str, value: ScalarType) -> str:
        return ';' + super().serialize_scalar(name, value)

    @classmethod
    def serialize_object(cls, name: str, value: ObjectType) -> str:
        return ';' + super().serialize_object(name, value)

    @classmethod
    def serialize_array(cls, name: str, value: ArrayType) -> str:
        return ';' + super().serialize_array(name, value)


class MatrixExplode(Matrix):
    @classmethod
    def serialize_array(cls, name: str, value: ArrayType) -> str:
        return ''.join(super().serialize_scalar(name, item) for item in value)

    @classmethod
    def serialize_object(cls, name: str, value: ObjectType) -> str:
        return ''.join(super().serialize_scalar(k, v) for k, v in value.items() if v)


# form


class FormExplode(BaseNamedSerializer):
    @classmethod
    def serialize_array(cls, name: str, value: ArrayType) -> str:
        return '&'.join(super().serialize_scalar(name, item) for item in value)

    @classmethod
    def serialize_object(cls, _name: str, value: ObjectType) -> str:
        return '&'.join(super().serialize_scalar(key, item) for key, item in value.items() if item)
