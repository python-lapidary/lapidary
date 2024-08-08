import typing_extensions as typing

if typing.TYPE_CHECKING:
    import httpx


class HTTPError(Exception):
    pass


class UnexpectedResponseError(HTTPError):
    def __init__(self, response: 'httpx.Response'):
        self.response = response


class ExpectedHTTPError(HTTPError):
    status_code: int
    body: typing.Any
    headers: typing.Any

    def __init__(self, status_code: int, body: typing.Any, headers: typing.Any):
        super().__init__()
        self.status_code = status_code
        self.headers = headers
        self.body = body


class ClientError(ExpectedHTTPError):
    pass


class ServerError(ExpectedHTTPError):
    pass
