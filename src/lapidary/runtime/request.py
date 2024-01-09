import httpx

from .compat import typing as ty
from .http_consts import ACCEPT, CONTENT_TYPE, MIME_JSON
from .mime import find_mime
from .model.op import OperationModel
from .model.params import serialize_param
from .model.request import RequestBodyModel
from .model.response_map import ResponseMap
from .param import ParamStyle
from .types_ import Serializer


class RequestFactory(ty.Protocol):
    def __call__(
            self,
            method: str,
            url: str,
            *,
            content: ty.Optional[httpx._types.RequestContent] = None,
            data: ty.Optional[httpx._types.RequestData] = None,
            files: ty.Optional[httpx._types.RequestFiles] = None,
            json: ty.Optional[ty.Any] = None,
            params: ty.Optional[httpx._types.QueryParamTypes] = None,
            headers: ty.Optional[httpx._types.HeaderTypes] = None,
            cookies: ty.Optional[httpx._types.CookieTypes] = None,
            timeout: ty.Union[httpx._types.TimeoutTypes, httpx._client.UseClientDefault] = httpx.USE_CLIENT_DEFAULT,
            extensions: ty.Optional[httpx._types.RequestExtensions] = None,
    ) -> httpx.Request:
        pass


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
    if model:
        for content_type, typ in model.serializers.items():
            if typ == type(obj):
                async def serialize(model):
                    for item in serialize_param(model, ParamStyle.simple, explode_list=False):
                        yield item.encode()

                return content_type, serialize

    raise TypeError(f'Unknown serializer for {type(obj)}')
