from typing import Optional, TypeVar, Generator

import httpx
import pydantic

from .params import ParamPlacement

try:
    from typing import TypeAlias
except ImportError:
    TypeAlias = TypeVar('TypeAlias')

PageFlowGenT: TypeAlias = Generator[httpx.Request, httpx.Response, None]


class ApiKeyAuth(httpx.Auth, pydantic.BaseSettings):
    api_key: str
    name: str
    placement: ParamPlacement
    value_prefix: Optional[str] = None

    def auth_flow(self, request: httpx.Request) -> PageFlowGenT:
        value = (self.value_prefix if self.value_prefix else '') + self.api_key
        request.headers[self.name] = value
        yield request
