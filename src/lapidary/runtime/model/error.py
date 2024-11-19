"""
Names of HttpErrorResponse and UnexpectedResponse don't end with `Error` in order to avoid double `Error` in the name.
So because both errors really wrap a HTTP response, both their names end with `Response` for consistency.
"""

from __future__ import annotations

import typing_extensions as typing

if typing.TYPE_CHECKING:
    import httpx


class LapidaryError(Exception):
    pass


class LapidaryResponseError(LapidaryError):
    """Base class for errors that wrap the response"""


Body = typing.TypeVar('Body')
Headers = typing.TypeVar('Headers')


class HttpErrorResponse(typing.Generic[Body, Headers], LapidaryResponseError):
    """
    Base error class for declared HTTP error responses - 4XX & 5XX.
    Python doesn't fully support parametrized exception types, but extending types can concretize it.
    """

    def __init__(self, status_code: int, headers: Headers, body: Body):
        super().__init__()
        self.status_code = status_code
        self.headers = headers
        self.body = body


class UnexpectedResponse(LapidaryResponseError):
    """Base error class for undeclared responses"""

    def __init__(self, response: httpx.Response):
        self.response = response
        self.content_type = response.headers.get('content-type')
