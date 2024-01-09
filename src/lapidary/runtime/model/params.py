import abc
import dataclasses as dc
import enum
from enum import Enum, unique
import uuid

import httpx

from ..compat import typing as ty


class ParamLocation(enum.Enum):
    cookie = 'cookie'
    header = 'header'
    path = 'path'
    query = 'query'


@unique
class ParamStyle(Enum):
    matrix = 'matrix'
    label = 'label'
    form = 'form'
    simple = 'simple'
    spaceDelimited = 'spaceDelimited'
    pipeDelimited = 'pipeDelimited'
    deepObject = 'deepObject'


@dc.dataclass(frozen=True)
class Param:
    alias: ty.Optional[str]

    location: ParamLocation

    style: ty.Optional[ParamStyle]
    explode: ty.Optional[bool]

    def get_style(self) -> ParamStyle:
        if self.style:
            return self.style
        return default_style[self.location]

    def get_explode(self) -> bool:
        return self.explode or self.get_style() == ParamStyle.form


@dc.dataclass(frozen=True)
class FullParam:
    alias: str

    location: ParamLocation

    style: ty.Optional[ParamStyle]
    explode: ty.Optional[bool]

    name: str
    type: ty.Type


@dc.dataclass(frozen=True)
class ParamAnnotation(abc.ABC):
    name: ty.Optional[str] = None
    """Name on OpenAPI side"""

    style: ty.Optional[ParamStyle] = None
    explode: ty.Optional[bool] = None


default_style = {
    ParamLocation.cookie: ParamStyle.form,
    ParamLocation.header: ParamStyle.simple,
    ParamLocation.path: ParamStyle.simple,
    ParamLocation.query: ParamStyle.form,
}


class ProcessedParams(ty.NamedTuple):
    """All information parsed from the function parameters"""
    query: httpx.QueryParams
    headers: httpx.Headers
    cookies: httpx.Cookies
    path: ty.Mapping[str, ty.Any]
    request_body: ty.Any


def serialize_param(value, style: ParamStyle, explode_list: bool) -> ty.Iterator[str]:
    if value is None:
        return
    elif isinstance(value, str):
        yield value
    elif isinstance(value, (
            int,
            float,
            uuid.UUID,
    )):
        yield str(value)
    elif isinstance(value, enum.Enum):
        yield value.value
    elif isinstance(value, list):
        values = [
            serialized
            for val in value
            for serialized in serialize_param(val, style, explode_list)]
        if explode_list:
            # httpx explodes lists, so just pass it thru
            yield from values
        else:
            yield ','.join(values)

    else:
        raise NotImplementedError(value)
