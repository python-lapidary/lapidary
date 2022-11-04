import enum
import uuid
from collections.abc import Generator
from enum import Enum, unique

import httpx
import pydantic

from .absent import ABSENT
from .params import ParamLocation


@unique
class ParamStyle(Enum):
    matrix = 'matrix'
    label = 'label'
    form = 'form'
    simple = 'simple'
    spaceDelimited = 'spaceDelimited'
    pipeDelimited = 'pipeDelimited'
    deepObject = 'deepObject'


default_style = {
    ParamLocation.cookie: ParamStyle.form,
    ParamLocation.header: ParamStyle.simple,
    ParamLocation.path: ParamStyle.simple,
    ParamLocation.query: ParamStyle.form,
}


def get_style(param: pydantic.fields.ModelField) -> ParamStyle:
    # allowed styles:
    # path: matrix, label, simple
    # query: form, spaceDelimited, pipeDelimited, deepObject
    # cookie: form,
    # header: simple

    location = param.field_info.extra['in_']
    return param.field_info.extra.get('style', default_style[location])


def process_params(model: pydantic.BaseModel) -> (httpx.QueryParams, httpx.Headers, httpx.Cookies):
    containers = {
        ParamLocation.cookie: [],
        ParamLocation.header: [],
        ParamLocation.query: [],
    }

    for attr_name, param in model.__fields__.items():
        param: pydantic.fields.ModelField
        value = getattr(model, attr_name)
        if value is ABSENT:
            continue

        param_name = param.alias
        placement = param.field_info.extra['in_']
        if placement is ParamLocation.path:
            continue

        style = get_style(param)

        value = [(param_name, value) for value in serialize_param(value, style, param.field_info.extra.get('explode'))]

        containers[placement].extend(value)

    return (
        httpx.QueryParams(containers[ParamLocation.query]),
        httpx.Headers(containers[ParamLocation.header]),
        httpx.Cookies(containers[ParamLocation.cookie])
    )


def serialize_param(value, style: ParamStyle, explode_list: bool) -> Generator[str, None, None]:
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
