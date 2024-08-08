import abc
import dataclasses as dc
from collections.abc import Mapping

import pydantic
import typing_extensions as typing

from .model.encode_param import FormExplode, SerializationStyle, Simple
from .types_ import MimeType, StatusCodeRange


class WebArg(abc.ABC):
    pass


@dc.dataclass
class Body(WebArg):
    content: Mapping[MimeType, type]


class Metadata(WebArg):
    """Annotation for models that hold other WebArg fields"""


class Param(WebArg, abc.ABC):
    style: type[SerializationStyle]
    alias: typing.Optional[str]

    def __init__(self, alias: typing.Optional[str], /, *, style: type[SerializationStyle]) -> None:
        self.alias = alias
        self.style = style


class Header(Param):
    def __init__(
        self,
        alias: typing.Optional[str] = None,
        /,
        *,
        style: type[SerializationStyle] = Simple,
    ) -> None:
        super().__init__(alias, style=style)


class Cookie(Param):
    def __init__(
        self,
        alias: typing.Optional[str] = None,
        /,
        *,
        style: type[SerializationStyle] = FormExplode,
    ) -> None:
        super().__init__(alias, style=style)


class Path(Param):
    def __init__(
        self,
        alias: typing.Optional[str] = None,
        /,
        *,
        style: type[SerializationStyle] = Simple,
    ) -> None:
        super().__init__(alias, style=style)


class Query(Param):
    def __init__(
        self,
        alias: typing.Optional[str] = None,
        /,
        *,
        style: type[SerializationStyle] = FormExplode,
    ) -> None:
        super().__init__(alias, style=style)


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
