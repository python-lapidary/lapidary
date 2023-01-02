from __future__ import annotations

from abc import abstractmethod
from collections.abc import ItemsView
from typing import Mapping, Any, TypeVar, Generic

from pydantic import BaseModel, root_validator, Extra, BaseConfig, parse_obj_as, fields


class ExtendableModel(BaseModel):
    """Base model class for model classes that accept extension fields, i.e. with keys start with 'x-'"""

    class Config(BaseConfig):
        extra = Extra.allow

    @root_validator(pre=True)
    def validate_extras(cls, values: Mapping[str, Any]) -> Mapping[str, Any]:
        if not values:
            return values
        aliases = (info.alias for info in cls.__fields__.values() if info.alias)

        for key, value in values.items():
            key: str
            if not (
                    key in cls.__fields__
                    or key in aliases
                    or key.startswith('x-')
            ):
                raise ValueError(f'{key} field not permitted')
        return values

    def __getitem__(self, item: str) -> Any:
        if not item.startswith('x-'):
            raise KeyError(item)
        return self.__dict__[item]


T = TypeVar('T')


class DynamicExtendableModel(Generic[T], BaseModel):
    """
    Base model class for classes with patterned fields of type T, ond extension fields (x-) of any type.
    This is equivalent of pydantic custom root type, where __root__: dict[str, T] but for keys starting with 'x-',
    it's __root__: dict[str, Any].

    Instances support accessing fields by index (e.g. paths['/']), which can return any existing attribute,
    as well as items() wich returns ItemsView with only pattern attributes.
    """

    class Config:
        extra = Extra.allow

    @root_validator
    def _validate_model(cls, values: Mapping[str, Any]):
        result = {}
        for key, value in values.items():
            if key.startswith('x-'):
                result[key] = value
            else:
                if not cls._validate_key(key):
                    raise ValueError(f'{key} field not permitted')
                this_superclass = next(cls_ for cls_ in cls.__orig_bases__ if cls_.__origin__ is DynamicExtendableModel)
                item_type = this_superclass.__args__[0]
                if not isinstance(value, item_type):
                    result[key] = parse_obj_as(item_type, value)
                else:
                    result[key] = value

        return result

    @classmethod
    @abstractmethod
    def _validate_key(cls, key: str) -> bool:
        pass

    def __getitem__(self, item: str) -> Any:
        return self.__dict__[item]

    def items(self) -> ItemsView[str, T]:
        """:returns: ItemsView (just like dict.items()) that excludes extension fields (those with keys starting with 'x-')"""
        return {key: value for key, value in self.__dict__.items() if not key.startswith('x-')}.items()

    def __contains__(self, item: str) -> bool:
        return item in self.__dict__

    def get(self, key: str, default_value: Any) -> Any:
        return self.__dict__.get(key, default_value)


def cross_validate_content(value, values: Mapping[str, Any], field: fields.ModelField):
    if values.get('content'):
        raise ValueError(f'{field.alias or field.name} not allowed when content is present')

    parsed = parse_obj_as(field.outer_type_, value) or parse_obj_as(field.type_, value)
    return parsed
