from typing import Optional, Generator

import httpx
import pydantic

from .params import ParamLocation

PageFlowGenT = Generator[httpx.Request, httpx.Response, None]


class ApiKeyAuth(httpx.Auth, pydantic.BaseSettings):
    api_key: str
    name: str
    placement: ParamLocation
    value_prefix: Optional[str] = None

    def auth_flow(self, request: httpx.Request) -> PageFlowGenT:
        value = (self.value_prefix if self.value_prefix else '') + self.api_key
        request.headers[self.name] = value
        yield request
