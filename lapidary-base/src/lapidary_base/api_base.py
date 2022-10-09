import logging
from typing import Optional, Any, TypeVar

import httpx
import pydantic.json

from ._params import process_params
from .pydantic_utils import to_model
from .request import get_accept_header
from .response import _handle_response, ResponseMap

T = TypeVar('T')

logger = logging.getLogger(__name__)


class ApiBase:
    def __init__(
            self, client: httpx.AsyncClient, global_response_map: Optional[ResponseMap] = None
    ):
        self._client = client
        self._global_response_map = global_response_map

    async def __aenter__(self) -> 'ApiBase':
        await self._client.__aenter__()
        return self

    async def __aexit__(self, __exc_type=None, __exc_value=None, __traceback=None, ) -> Optional[bool]:
        return await self._client.__aexit__(__exc_type, __exc_value, __traceback)

    async def aclose(self) -> None:
        await self.__aexit__()

    async def _request(
            self,
            method: str,
            url: str,
            param_model: Optional[pydantic.BaseModel] = None,
            request_body: Any = None,
            response_map: Optional[ResponseMap] = None,
            auth: Optional[httpx.Auth] = None,
    ) -> T:
        request = self._build_request(method, url, param_model, request_body, response_map)

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("%s", f'{request.method} {request.url} {request.headers}')

        response = await self._client.send(request, auth=auth)

        return self._handle_response(response, response_map)

    def _build_request(
            self,
            method: str,
            url: str,
            param_model: Optional[pydantic.BaseModel],
            request_body: Any,
            response_map: Optional[ResponseMap],
    ) -> httpx.Request:
        if param_model:
            params, headers, cookies = process_params(param_model)
        else:
            params = cookies = None
            headers = httpx.Headers()

        if request_body is not None:
            headers['content-type'] = 'application/json'

        if (accept := get_accept_header(response_map, self._global_response_map)) is not None:
            headers['accept'] = accept

        if not isinstance(request_body, pydantic.BaseModel) and request_body is not None:
            request_body = to_model(request_body)

        content = (
            request_body.json(by_alias=True, exclude_unset=True, exclude_defaults=True)
            if request_body is not None
            else None
        )

        return self._client.build_request(
            method, url, content=content, params=params, headers=headers, cookies=cookies,
        )

    def _handle_response(
            self, response: httpx.Response, response_map: Optional[ResponseMap]
    ):
        return _handle_response(response, response_map, self._global_response_map)
