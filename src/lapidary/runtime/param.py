import dataclasses as dc
from typing import Optional

import typing_extensions as typing

from ._httpx import ParamValue
from .model.encode_param import ParamStyle
from .model.params import Param

if typing.TYPE_CHECKING:
    from .model.request import RequestBuilder


class Cookie(Param):
    def __init__(
        self,
        alias: Optional[str] = None,
        /,
        *,
        style: ParamStyle = ParamStyle.form,
        explode: Optional[bool] = None,
    ) -> None:
        super().__init__(alias, style=style, explode=explode)

    def _apply(self, builder: 'RequestBuilder', value: typing.Any) -> None:
        builder.cookies[self.http_name] = value


@dc.dataclass
class Header(Param):
    def __init__(
        self,
        alias: Optional[str] = None,
        /,
        *,
        style: ParamStyle = ParamStyle.simple,
        explode: Optional[bool] = None,
    ) -> None:
        super().__init__(alias, style=style, explode=explode)

    def _apply(self, builder: 'RequestBuilder', value: ParamValue) -> None:
        builder.headers[self.http_name] = str(value)


@dc.dataclass
class Path(Param):
    def __init__(
        self,
        alias: Optional[str] = None,
        /,
        *,
        style: ParamStyle = ParamStyle.simple,
        explode: Optional[bool] = None,
    ) -> None:
        super().__init__(alias, style=style, explode=explode)

    def _apply(self, builder: 'RequestBuilder', value: typing.Any) -> None:
        builder.path_params[self.http_name] = value


@dc.dataclass
class Query(Param):
    def __init__(
        self,
        alias: Optional[str] = None,
        /,
        *,
        style: ParamStyle = ParamStyle.form,
        explode: Optional[bool] = None,
    ) -> None:
        super().__init__(alias, style=style, explode=explode)

    def _apply(self, builder: 'RequestBuilder', value: typing.Any) -> None:
        builder.query_params.append((self.http_name, value))
