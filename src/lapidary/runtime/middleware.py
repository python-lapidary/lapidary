import abc
from typing import Generic, TypeVar

import httpx

State = TypeVar('State')


class HttpxMiddleware(Generic[State]):
    """
    Base class for HTTP middleware.
    """

    @abc.abstractmethod
    async def handle_request(self, request: httpx.Request) -> State:
        """Called for each request after it's generated for a method call but before it's sent to the remote server.
        Any returned value will be passed back to handle_response.
        """

    async def handle_response(self, response: httpx.Response, request: httpx.Request, state: State) -> None:
        """Called for each response after it's been received from the remote server and before it's converted to the return type as defined
        in the python method.

        state is the value returned by handle_request
        """
