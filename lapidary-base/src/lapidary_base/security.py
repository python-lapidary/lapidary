from typing import Optional, Generator

import httpx
import pydantic

from .params import ParamLocation

PageFlowGenT = Generator[httpx.Request, httpx.Response, None]


class ApiKeyAuth(httpx.Auth, pydantic.BaseSettings):
    api_key: str
    name: str
    placement: ParamLocation

    def auth_flow(self, request: httpx.Request) -> PageFlowGenT:
        value = self.api_key
        if self.placement is ParamLocation.header:
            request.headers[self.name] = value
        elif self.placement is ParamLocation.query:
            request.url.params[self.name] = value
        elif self.placement is ParamLocation.cookie:
            # TODO
            raise NotImplementedError(ParamLocation.cookie)
        else:
            raise ValueError(self.placement)
        yield request


class HTTPAuth(ApiKeyAuth):
    def __init__(self, scheme: str, token: str, bearer_format: Optional[str] = None):
        value_format = 'Bearer {token}' if scheme.lower() == 'bearer' else bearer_format
        super().__init__(
            api_key=value_format.format(token=token),
            name='Authorization',
            placement=ParamLocation.header,
        )
