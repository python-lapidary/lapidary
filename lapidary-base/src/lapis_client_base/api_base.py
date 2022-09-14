from typing import Callable, Generator, TypeAlias, Optional, Any, Type

import httpx
from pydantic import BaseModel

from .absent import ABSENT
from .params import ParamPlacement

PageFlowGenT: TypeAlias = Generator[httpx.Request, httpx.Response, None]
PageFlowCallableT: TypeAlias = Callable[[Callable[[httpx.QueryParams], httpx.Request]], PageFlowGenT]


class ApiBase:
    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    async def _request(self, method: str, url: str, param_model: Optional[BaseModel] = None, response_mapping: Optional[dict[str, Type]] = None):
        request = self._build_request(method, url, param_model)
        response = await self._client.send(request)
        return _handle_response(response, response_mapping)

    def _build_request(self, method: str, url: str, param_model: Optional[BaseModel] = None) -> httpx.Request:
        if param_model:
            params, headers, cookies = process_params(param_model)
        else:
            params = headers = cookies = None
        return self._client.build_request(method, url, params=params, headers=headers, cookies=cookies)


def _handle_response(response: httpx.Response, response_mapping: Optional[dict[str, Type]] = None) -> Any:
    if response_mapping:
        response_obj = resolve_response(response, response_mapping)
        if isinstance(response_obj, Exception):
            raise response_obj
        else:
            return response_obj
    else:
        response.raise_for_status()
        return response.json()


def process_params(model: BaseModel) -> (httpx.QueryParams, httpx.Headers, httpx.Cookies):
    query = {}
    headers = httpx.Headers()
    cookies = httpx.Cookies()

    for attr_name, param in model.__fields__.items():
        value = getattr(model, attr_name)
        if value is ABSENT:
            continue

        param_name = param.field_info.extra['param_name']
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


def resolve_response(response: httpx.Response, mapping: dict[str, Type]) -> Any:
    typ = find_code_mapping(str(response.status_code), mapping)
    data = response.json()
    if typ is not None:
        return typ(**data)
    else:
        response.raise_for_status()
        return data


def find_code_mapping(code: str, mapping: dict) -> Optional[Type]:
    for match in _status_code_matches(code):
        if match in mapping:
            return mapping[match]
    else:
        return None


def _status_code_matches(code: str) -> Generator[str, None, None]:
    yield code

    code_as_list = list(code)
    for pos in [-1, -2]:
        code_as_list[pos] = 'X'
        yield ''.join(code_as_list)

    yield 'default'
