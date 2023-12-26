import enum
from typing import Any, Callable, Mapping, Optional

import httpx
import pydantic

from ._params import process_params
from .http_consts import ACCEPT, CONTENT_TYPE, MIME_JSON
from .mime import find_mime
from .model import OperationModel, ParamLocation, ResponseMap

RequestFactory = Callable[..., httpx.Request]


def get_accept_header(response_map: Optional[ResponseMap], global_response_map: Optional[ResponseMap]) -> Optional[str]:
    all_mime_types = {
        mime
        for rmap in [response_map, global_response_map]
        if rmap
        for mime_map in rmap.values()
        for mime in mime_map.keys()
    }
    return find_mime(all_mime_types, MIME_JSON)


def build_request(  # pylint: disable=too-many-arguments
        operation: OperationModel,
        actual_params: Mapping[str, Any],
        request_body: Any,
        response_map: Optional[ResponseMap],
        global_response_map: Optional[ResponseMap],
        request_factory: RequestFactory,
) -> httpx.Request:
    query_params: Optional[httpx.QueryParams]
    cookies: Optional[httpx.Cookies]
    path_params: Optional[Mapping[str, str]]

    if actual_params:
        query_params, headers, cookies, path_params = process_params(operation.params, actual_params)
    else:
        cookies = path_params = query_params = None
        headers = httpx.Headers()

    url = operation.path.format_map(path_params) if path_params else operation.path

    if request_body is not None:
        headers[CONTENT_TYPE] = MIME_JSON

    if (accept := get_accept_header(response_map, global_response_map)) is not None:
        headers[ACCEPT] = accept

    content = (
        request_body.json(by_alias=True, exclude_unset=True, exclude_defaults=True)
        if request_body is not None
        else None
    )

    return request_factory(
        operation.method,
        url,
        content=content,
        params=query_params,
        headers=headers,
        cookies=cookies,
    )


def get_path(path_format: str, param_model: pydantic.BaseModel) -> str:
    path_params = {
        param_name: param_to_str(param_model.__dict__[param_name])
        for param_name in param_model.model_fields
        if param_model.model_fields[param_name].json_schema_extra['in_'] is ParamLocation.path
    } if param_model else {}
    return path_format.format(**path_params)


def param_to_str(value: Any) -> str:
    if isinstance(value, enum.Enum):
        return value.value
    return str(value)
