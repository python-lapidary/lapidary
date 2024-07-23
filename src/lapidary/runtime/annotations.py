import abc
import dataclasses as dc
from collections.abc import Mapping

import pydantic
import typing_extensions as typing

from .model.encode_param import ParamStyle
from .types_ import MimeType, ResponseCode


class WebArg(abc.ABC):
    pass


@dc.dataclass
class Body(WebArg):
    content: Mapping[MimeType, type]


class Metadata(WebArg):
    """Annotation for models that hold other WebArg fields"""


class Param(WebArg, abc.ABC):
    style: ParamStyle
    alias: typing.Optional[str]
    explode: bool

    def __init__(self, alias: typing.Optional[str], /, *, style: ParamStyle, explode: bool) -> None:
        self.alias = alias
        self.style = style
        self.explode = explode


class Header(Param):
    def __init__(
        self,
        alias: typing.Optional[str] = None,
        /,
        *,
        style: ParamStyle = ParamStyle.simple,
        explode: typing.Optional[bool] = None,
    ) -> None:
        super().__init__(alias, style=style, explode=explode if explode is not None else style == ParamStyle.form)


class Cookie(Param):
    def __init__(
        self,
        alias: typing.Optional[str] = None,
        /,
        *,
        style: ParamStyle = ParamStyle.form,
        explode: typing.Optional[bool] = None,
    ) -> None:
        super().__init__(alias, style=style, explode=explode if explode is not None else style == ParamStyle.form)


class Path(Param):
    def __init__(
        self,
        alias: typing.Optional[str] = None,
        /,
        *,
        style: ParamStyle = ParamStyle.simple,
        explode: typing.Optional[bool] = None,
    ) -> None:
        super().__init__(alias, style=style, explode=explode if explode is not None else style == ParamStyle.form)


class Query(Param):
    def __init__(
        self,
        alias: typing.Optional[str] = None,
        /,
        *,
        style: ParamStyle = ParamStyle.form,
        explode: typing.Optional[bool] = None,
    ) -> None:
        super().__init__(alias, style=style, explode=explode if explode is not None else style == ParamStyle.form)


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
    responses: Mapping[ResponseCode, Response]
