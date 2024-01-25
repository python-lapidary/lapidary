import dataclasses as dc

from .compat import typing as ty
from .model.params import Param, ParamStyle
from .types_ import ParamValue

if ty.TYPE_CHECKING:
    from .model.request import RequestBuilder


@dc.dataclass
class Cookie(Param):
    style: ParamStyle = ParamStyle.form

    def _apply(self, builder: 'RequestBuilder', name: str, value: ty.Any) -> None:
        builder.cookies[name] = value


@dc.dataclass
class Header(Param):
    style: ParamStyle = ParamStyle.simple

    def _apply(self, builder: 'RequestBuilder', name: str, value: ParamValue) -> None:
        builder.headers[name] = str(value)


@dc.dataclass
class Path(Param):
    style: ParamStyle = ParamStyle.simple

    def _apply(self, builder: 'RequestBuilder', name: str, value: ty.Any) -> None:
        builder.path_params[name] = value


@dc.dataclass
class Query(Param):
    style: ParamStyle = dc.field(default=ParamStyle.form)

    def _apply(self, builder: 'RequestBuilder', name: str, value: ty.Any) -> None:
        builder.query_params[name] = value
