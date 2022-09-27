import logging
from typing import Generator, Optional, Type, TypeVar, Iterable

import httpx
import pydantic

from .absent import ABSENT
from .params import ParamPlacement

T = TypeVar('T')

logger = logging.getLogger(__name__)


class ApiBase:
    def __init__(
            self, client: httpx.AsyncClient, global_response_map: Optional[dict[str, dict[str, Type]]] = None
    ):
        self._client = client
        self._global_response_map = global_response_map

    async def _request(
            self,
            method: str,
            url: str,
            param_model: Optional[pydantic.BaseModel] = None,
            request_body: Optional[pydantic.BaseModel] = None,
            response_map: Optional[dict[str, dict[str, Type]]] = None,
            auth: Optional[httpx.Auth] = None,
    ) -> T:
        request = self._build_request(method, url, param_model, request_body)

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("%s", f'{request.method} {request.url} {request.headers}')

        response = await self._client.send(request, auth=auth)

        if self._global_response_map is not None:
            full_response_map = self._global_response_map.copy()
            full_response_map.update(response_map)
        else:
            full_response_map = response_map

        return _handle_response(response, full_response_map)

    def _build_request(
            self,
            method: str,
            url: str,
            param_model: Optional[pydantic.BaseModel] = None,
            request_body: Optional[pydantic.BaseModel] = None,
    ) -> httpx.Request:
        if param_model:
            params, headers, cookies = process_params(param_model)
        else:
            params = headers = cookies = None

        data = request_body.dict(by_alias=True, exclude_unset=True, exclude_defaults=True) if request_body is not None else None

        return self._client.build_request(method, url, data=data, params=params, headers=headers, cookies=cookies)


def _handle_response(response: httpx.Response, response_mapping: Optional[dict[str, dict[str, Type[T]]]] = None) -> T:
    if response_mapping:
        response_obj = resolve_response(response, response_mapping)
        if isinstance(response_obj, Exception):
            raise response_obj
        else:
            return response_obj
    else:
        response.raise_for_status()
        return response.json()


def process_params(model: pydantic.BaseModel) -> (httpx.QueryParams, httpx.Headers, httpx.Cookies):
    query = {}
    headers = httpx.Headers()
    cookies = httpx.Cookies()

    for attr_name, param in model.__fields__.items():
        value = getattr(model, attr_name)
        if value is ABSENT:
            continue

        param_name = param.alias
        placement = param.field_info.extra['in_']
        if placement == ParamPlacement.cookie:
            cookies[param_name] = value
        elif placement == ParamPlacement.header:
            headers[param_name] = value
        elif placement == ParamPlacement.query:
            query[param_name] = value
        elif placement == ParamPlacement.path:
            # handled by the operation method
            continue
        else:
            raise ValueError(placement)

    return httpx.QueryParams(query), headers, cookies


def resolve_response(response: httpx.Response, mapping: dict[str, dict[str, Type[T]]]) -> T:
    code_match = find_code_mapping(str(response.status_code), mapping)
    if code_match is None:
        response.raise_for_status()
        return response.json()

    mime_mapping = mapping[code_match]
    mime_match = find_mime(mime_mapping.keys(), response.headers['content-type'])

    data = response.json()
    if mime_match is not None:
        typ = mime_mapping[mime_match]
        try:
            return pydantic.parse_obj_as(typ, data)
        except pydantic.ValidationError:
            raise ValueError('Error parsing response as type', typ)
    else:
        response.raise_for_status()
        return data


def find_code_mapping(code: str, mapping: dict[str, dict[str, Type]]) -> Optional[str]:
    for code_match in _status_code_matches(code):
        if code_match in mapping:
            return code_match
    else:
        return None


def find_mime(supported_mimes: Iterable[str], response_mime: str) -> str:
    from mimeparse import best_match
    match = best_match(supported_mimes, response_mime)
    return match if match != '' else None


def _status_code_matches(code: str) -> Generator[str, None, None]:
    yield code

    code_as_list = list(code)
    for pos in [-1, -2]:
        code_as_list[pos] = 'X'
        yield ''.join(code_as_list)

    yield 'default'
