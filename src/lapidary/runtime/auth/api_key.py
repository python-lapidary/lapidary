from dataclasses import dataclass

import httpx

from .common import PageFlowGenT
from .. import openapi
from ..model.params import ParamLocation


@dataclass(eq=False, order=False, frozen=True)
class APIKey:
    api_key: str

    def create(self, model: openapi.APIKeySecurityScheme) -> httpx.Auth:
        return ApiKeyAuth(
            api_key=self.api_key,
            name=model.name,
            placement=ParamLocation[model.in_.value],
        )


@dataclass(eq=False, order=False, frozen=True)
class ApiKeyAuth(httpx.Auth):
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
