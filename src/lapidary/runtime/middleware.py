import abc
from typing import Generic, TypeVar

import httpx

State = TypeVar('State')


class HttpxMiddleware(Generic[State]):
    @abc.abstractmethod
    async def handle_request(self, request: httpx.Request) -> State:
        pass

    async def handle_response(self, response: httpx.Response, request: httpx.Request, state: State) -> None:
        pass
