from typing import Generator, Protocol, Any, Union, TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from httpx._client import UseClientDefault

AuthT = Union[httpx.Auth, 'UseClientDefault', None]
PageFlowGenT = Generator[httpx.Request, httpx.Response, None]


class AuthParamModel(Protocol):
    def create(self, model: Any) -> httpx.Auth:
        pass
