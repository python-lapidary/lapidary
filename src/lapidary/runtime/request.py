import httpx

from .compat import typing as ty
from .http_consts import ACCEPT, CONTENT_TYPE, MIME_JSON
from .mime import find_mime
from .model import ResponseMap
from .model.op import OperationModel
from .model.request import RequestBodyModel
from .types_ import Serializer

# accepts parameters of httpx.Client.build_request
RequestFactory = ty.Callable[..., httpx.Request]


def get_accept_header(response_map: ty.Optional[ResponseMap]) -> ty.Optional[str]:
    all_mime_types = {
        mime
        for mime_map in response_map.values()
        for mime in mime_map.keys()
    }
    return find_mime(all_mime_types, MIME_JSON)


def build_request(
        operation: OperationModel,
        actual_params: ty.Mapping[str, ty.Any],
        request_factory: RequestFactory,
) -> httpx.Request:
    query_params, headers, cookies, path_params, request_body = operation.process_params(actual_params)

    url = operation.path.format_map(path_params)

    if request_body is not None:
        if not operation.request_body:
            raise ValueError('Unexpected request body')
        content_type, serializer = find_request_body_serializer(operation.request_body, request_body)
        headers[CONTENT_TYPE] = content_type
        content = serializer(request_body)
    else:
        content = None

    if (accept := get_accept_header(operation.response_map)) is not None:
        headers[ACCEPT] = accept

    return request_factory(
        operation.method,
        url,
        content=content,
        params=query_params,
        headers=headers,
        cookies=cookies,
    )


def find_request_body_serializer(
        model: ty.Optional[RequestBodyModel],
        obj: ty.Any,
) -> ty.Tuple[str, Serializer]:

    # find the serializer by type
    obj_type = type(obj)

    for content_type, ser_info in model.serializers.items():
        type_, serializer = ser_info
        if type_ == obj_type:
            return content_type, serializer

    raise TypeError(f'Unknown serializer for {type(obj)}')
