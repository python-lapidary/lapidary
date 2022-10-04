import logging
from types import TracebackType
from typing import Optional, Type, Any

import httpx
import pydantic

from .absent import ABSENT
from .params import ParamPlacement
from .response import _handle_response, T

logger = logging.getLogger(__name__)


class ApiBase:
    def __init__(
            self, client: httpx.AsyncClient, global_response_map: Optional[dict[str, dict[str, Type]]] = None
    ):
        self._client = client
        self._global_response_map = global_response_map

    async def __aenter__(self) -> 'ApiBase':
        await self._client.__aenter__()
        return self

    async def __aexit__(
            self,
            __exc_type: Optional[Type[BaseException]] = None,
            __exc_value: Optional[BaseException] = None,
            __traceback: Optional[TracebackType] = None,
    ) -> Optional[bool]:
        return await self._client.__aexit__(__exc_type, __exc_value, __traceback)

    async def aclose(self) -> None:
        await self.__aexit__()

    async def _request(
            self,
            method: str,
            url: str,
            param_model: Optional[pydantic.BaseModel] = None,
            request_body: Any = None,
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

        if not isinstance(request_body, pydantic.BaseModel):
            from pydantic.tools import _get_parsing_type
            model_type = _get_parsing_type(type(request_body))
            request_body = model_type(__root__=request_body)

        content = (
            request_body.json(by_alias=True, exclude_unset=True, exclude_defaults=True)
            if request_body is not None
            else None)

        return self._client.build_request(
            method, url, content=content, params=params, headers=headers, cookies=cookies,
        )


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
