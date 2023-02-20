from __future__ import annotations

import enum

import pydantic

__all__ = [
    'LapidaryModelType',
    'PluginModel',
]


class PluginModel(pydantic.BaseModel):
    """Model for plugin configuration"""

    factory: str
    """Name of class or callable that returns a Plugin instance, in "module:name" format."""


class LapidaryModelType(enum.Enum):
    MODEL = 'model'
    """The default type, rendered as a subclass of pydantic.BaseModel."""

    EXCEPTION = 'exception'
    """Error typy, not used as return type, if received, it's raised."""

    ITERATOR = 'iterator'
    """
    If the received object is an Iterable, it's returned as an Iterator.
    Mappings are returned as an iterators of tuples of the keys-value pairs.

    Particularly useful in combination with a paging plugin.
    """
