import logging
from typing import Callable, Generator, Optional, Type, TypeVar, Iterable

try:
    from typing import TypeAlias
except ImportError:
    TypeAlias = TypeVar('TypeAlias')

import httpx
import pydantic

from .absent import ABSENT
from .params import ParamPlacement

PageFlowGenT: TypeAlias = Generator[httpx.Request, httpx.Response, None]
PageFlowCallableT: TypeAlias = Callable[[Callable[[httpx.QueryParams], httpx.Request]], PageFlowGenT]

T = TypeVar('T')
logger = logging.getLogger(__name__)


class ApiBase:
    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    async def _request(
            self,
            method: str,
            url: str,
            param_model: Optional[pydantic.BaseModel] = None,
            response_mapping: Optional[dict[str, dict[str, Type]]] = None
    ) -> T:
        request = self._build_request(method, url, param_model)

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("%s", f'{request.method} {request.url} {request.headers}')

        response = await self._client.send(request)
        return _handle_response(response, response_mapping)

    def _build_request(self, method: str, url: str, param_model: Optional[pydantic.BaseModel] = None) -> httpx.Request:
        if param_model:
            params, headers, cookies = process_params(param_model)
        else:
            params = headers = cookies = None
        return self._client.build_request(method, url, params=params, headers=headers, cookies=cookies)


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
