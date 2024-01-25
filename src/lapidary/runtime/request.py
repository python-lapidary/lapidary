import httpx

from .compat import typing as ty
from .http_consts import ACCEPT, MIME_JSON
from .mime import find_mime
from .model.response_map import ResponseMap
from .model.op import OperationModel
from .model.request import RequestFactory, RequestBuilder


def get_accept_header(response_map: ty.Optional[ResponseMap]) -> ty.Optional[str]:
    if not response_map:
        return None

    all_mime_types = {
        mime
        for mime_map in response_map.values()
        for mime in mime_map.keys()
    }
    return find_mime(all_mime_types, MIME_JSON)


def build_request(
        operation: 'OperationModel',
        actual_params: ty.Mapping[str, ty.Any],
        request_factory: 'RequestFactory',
) -> tuple[httpx.Request, ty.Optional[httpx.Auth]]:
    builder = RequestBuilder(
        request_factory,
        operation.method,
        operation.path,
    )
    operation.process_params(actual_params, builder)

    if ACCEPT not in builder.headers and (accept := get_accept_header(operation.response_map)) is not None:
        builder.headers[ACCEPT] = accept

    return builder()
