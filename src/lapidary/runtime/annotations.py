import abc
import dataclasses as dc
from collections.abc import Mapping

import pydantic
import typing_extensions as typing

from .model.param_serialization import FormExplode, MultimapSerializationStyle, SimpleMultimap, SimpleString, StringSerializationStyle
from .types_ import MimeType, StatusCodeRange


class WebArg(abc.ABC):
    pass


@dc.dataclass
class Body(WebArg):
    content: Mapping[MimeType, type]


class Metadata(WebArg):
    """Annotation for models that hold other WebArg fields"""


class Param(WebArg, abc.ABC):
    style: typing.Any
    alias: typing.Optional[str]

    def __init__(self, alias: typing.Optional[str], /) -> None:
        self.alias = alias


class Header(Param):
    def __init__(
        self,
        alias: typing.Optional[str] = None,
        /,
        *,
        style: type[MultimapSerializationStyle] = SimpleMultimap,
    ) -> None:
        super().__init__(alias)
        self.style = style


class Cookie(Param):
    def __init__(
        self,
        alias: typing.Optional[str] = None,
        /,
        *,
        style: type[MultimapSerializationStyle] = FormExplode,
    ) -> None:
        super().__init__(alias)
        self.style = style


class Path(Param):
    def __init__(
        self,
        alias: typing.Optional[str] = None,
        /,
        *,
        style: type[StringSerializationStyle] = SimpleString,
    ) -> None:
        super().__init__(alias)
        self.style = style


class Query(Param):
    def __init__(
        self,
        alias: typing.Optional[str] = None,
        /,
        *,
        style: type[MultimapSerializationStyle] = FormExplode,
    ) -> None:
        super().__init__(alias)
        self.style = style


@dc.dataclass
class Link(WebArg):
    alias: str


class StatusCode(WebArg):
    pass


@dc.dataclass
class Response:
    body: Body
    headers: typing.Optional[type[pydantic.BaseModel]] = None


@dc.dataclass
class Responses(WebArg):
    responses: Mapping[StatusCodeRange, Response]
