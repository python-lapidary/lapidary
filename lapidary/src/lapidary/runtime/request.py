import enum
import typing
from typing import Optional, Any, Union

import httpx
import pydantic

from ._params import process_params
from .http_consts import MIME_JSON, CONTENT_TYPE, ACCEPT
from .mime import find_mime
from .model import ResponseMap, ParamLocation
from .pydantic_utils import to_model


def get_accept_header(response_map: Optional[ResponseMap], global_response_map: Optional[ResponseMap]) -> Optional[str]:
    all_mime_types = {
        mime
        for rmap in [response_map, global_response_map]
        if rmap is not None
        for mime_map in rmap.values()
        for mime in mime_map.keys()
    }
    return find_mime(all_mime_types, MIME_JSON)


class RequestParts(typing.TypedDict):
    content: Union[str, bytes, None]
    params: Optional[httpx.QueryParams]
    headers: Optional[httpx.Headers]
    cookies: Optional[httpx.Cookies]


def build_request(
        param_model: Optional[pydantic.BaseModel],
        request_body: Any,
        response_map: Optional[ResponseMap],
        global_response_map: Optional[ResponseMap],
) -> RequestParts:
    if param_model:
        params, headers, cookies = process_params(param_model)
    else:
        params = cookies = None
        headers = httpx.Headers()

    if request_body is not None:
        headers[CONTENT_TYPE] = MIME_JSON

    if (accept := get_accept_header(response_map, global_response_map)) is not None:
        headers[ACCEPT] = accept

    if not isinstance(request_body, pydantic.BaseModel) and request_body is not None:
        request_body = to_model(request_body)

    content = (
        request_body.json(by_alias=True, exclude_unset=True, exclude_defaults=True)
        if request_body is not None
        else None
    )

    return dict(
        content=content,
        params=params,
        headers=headers,
        cookies=cookies
    )


def get_path(path_format: str, param_model: pydantic.BaseModel) -> str:
    path_params = {
        param_name: param_to_str(param_model.__dict__[param_name])
        for param_name in param_model.__fields_set__
        if param_model.__fields__[param_name].field_info.extra['in_'] is ParamLocation.path
    }
    return path_format.format(**path_params)


def param_to_str(value: Any) -> str:
    if isinstance(value, enum.Enum):
        return value.value
    return str(value)
