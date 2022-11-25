from typing import Generator, Protocol, Any

import httpx

PageFlowGenT = Generator[httpx.Request, httpx.Response, None]


class AuthParamModel(Protocol):
    def create(self, model: Any) -> httpx.Auth:
        pass
