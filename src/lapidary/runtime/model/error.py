import typing_extensions as typing

if typing.TYPE_CHECKING:
    import httpx


class HTTPError(Exception):
    pass


class UnexpectedResponseError(HTTPError):
    def __init__(self, response: 'httpx.Response'):
        self.response = response
