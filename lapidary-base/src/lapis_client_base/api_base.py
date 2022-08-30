from typing import Callable, Generator, TypeAlias

import httpx

PageFlowGenT: TypeAlias = Generator[httpx.Request, httpx.Response, None]
PageFlowCallableT: TypeAlias = Callable[[Callable[[httpx.QueryParams], httpx.Request]], PageFlowGenT]


class ApiBase:
    def __init__(self, client: httpx.AsyncClient):
        self._client = client
