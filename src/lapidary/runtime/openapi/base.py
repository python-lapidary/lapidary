from __future__ import annotations

from abc import abstractmethod
from collections.abc import ItemsView, Mapping
import inspect
import typing as ty

import pydantic

from .. import pydantic_utils


class ExtendableModel(pydantic.BaseModel):
    """Base model class for model classes that accept extension fields, i.e. with keys start with 'x-'"""

    model_config = pydantic.ConfigDict(
        extra='allow',
    )

    @pydantic.model_validator(mode='before')
    @classmethod
    def validate_extras(cls, data: ty.Mapping[str, ty.Any]) -> ty.Mapping[str, ty.Any]:  # pylint: disable=no-self-argument
        if not data or not isinstance(data, dict):
            return data

        aliases = tuple(info.alias for info in cls.model_fields.values() if info.alias)

        for key in data.keys():
            if not (
                    key in cls.model_fields
                    or key in aliases
                    or key.startswith('x-')
            ):
                raise ValueError(f'{key} field not permitted')
        return data

    def __getitem__(self, item: str) -> ty.Any:
        if not item.startswith('x-'):
            raise KeyError(item)
        return self.__dict__[item]


T = ty.TypeVar('T')


class DynamicExtendableModel(pydantic.BaseModel, ty.Generic[T]):
    """
    Base model class for classes with patterned fields of type T, ond extension fields (x-) of any type.
    This is equivalent of pydantic custom root type, where __root__: dict[str, T] but for keys starting with 'x-',
    it's __root__: dict[str, Any].

    Instances support accessing fields by index (e.g. paths['/']), which can return any existing attribute,
    as well as items() which returns ItemsView with only pattern attributes.
    """

    model_config = pydantic.ConfigDict(
        extra='allow'
    )

    @pydantic.model_validator(mode='before')
    @classmethod
    def _validate_model(cls, values: Mapping[str, ty.Any]):  # pylint: disable=no-self-argument
        if not isinstance(values, Mapping):
            return values
        result = {}
        for key, value in values.items():
            if key.startswith('x-'):
                result[key] = value
            else:
                if not cls._validate_key(key):
                    raise ValueError(f'{key} field not permitted')

                for typ in inspect.getmro(cls):
                    if o := pydantic_utils.get_origin(typ):
                        if o is DynamicExtendableModel:
                            item_type = pydantic_utils.get_args(typ)[0]
                assert item_type

                if not isinstance(value, item_type):
                    result[key] = pydantic.TypeAdapter(item_type).validate_python(value)
                else:
                    result[key] = value

        return result

    @classmethod
    @abstractmethod
    def _validate_key(cls, key: str) -> bool:
        pass

    def __getitem__(self, item: str) -> ty.Any:
        return self.__pydantic_extra__[item]

    def items(self) -> ItemsView[str, T]:
        """:returns: ItemsView (just like dict.items()) that excludes extension fields (those with keys starting with 'x-')"""
        return {key: value for key, value in self.__pydantic_extra__.items() if not key.startswith('x-')}.items()

    def __contains__(self, item: str) -> bool:
        return item in self.__pydantic_extra__

    def get(self, key: str, default_value: ty.Any = None) -> ty.Any:
        return self.__pydantic_extra__.get(key, default_value)


def cross_validate_content(values: Mapping[str, ty.Any]) -> Mapping[str, ty.Any]:
    if 'content' not in values:
        return values

    for key in ('style', 'explode', 'allowReserved', 'schema_', 'example', 'examples'):
        if key in values:
            raise ValueError(key)

    return values


def ref_discriminator(d: dict[str, ty.Any]) -> bool:
    return '$ref' in d
