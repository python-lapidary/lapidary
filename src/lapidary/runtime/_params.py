import enum
import uuid
from typing import Any, Tuple, List, Iterator, Mapping, Iterable

import httpx

from .absent import ABSENT
from .model.params import ParamLocation, Param, ParamStyle


def process_params(
        model: Iterable[Param], actual_params: Mapping[str, Any]
) -> Tuple[httpx.QueryParams, httpx.Headers, httpx.Cookies, Mapping[str, str]]:
    formal_params: Mapping[str, Param] = {param.name: param for param in model}
    containers: Mapping[ParamLocation, List[Any]] = {
        ParamLocation.cookie: [],
        ParamLocation.header: [],
        ParamLocation.query: [],
        ParamLocation.path: [],
    }

    for param_name, value in actual_params.items():
        if value is ABSENT:
            continue

        formal_param = formal_params.get(param_name)
        if not formal_param:
            continue

        formal_param: Param  # type: ignore[no-redef]
        placement = formal_param.location

        value = [(formal_param.alias, value) for value in serialize_param(value, formal_param.style, formal_param.explode)]
        containers[placement].extend(value)

    return (
        httpx.QueryParams(containers[ParamLocation.query]),
        httpx.Headers(containers[ParamLocation.header]),
        httpx.Cookies(containers[ParamLocation.cookie]),
        {item[0]: item[1] for item in containers[ParamLocation.path]},
    )


def serialize_param(value, style: ParamStyle, explode_list: bool) -> Iterator[str]:
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
