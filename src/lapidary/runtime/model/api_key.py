import httpx
import httpx_auth.authentication as authx

from ..compat import typing as ty


class CookieApiKey(httpx.Auth, authx.SupportMultiAuth):
    """Describes an API Key requests authentication."""

    def __init__(self, api_key: str, cookie_name: ty.Optional[str] = None):
        """
        :param api_key: The API key that will be sent.
        :param cookie_name: Name of the query parameter. "api_key" by default.
        """
        self.api_key = api_key
        if not api_key:
            raise ValueError("API Key is mandatory.")
        self.cookie_parameter_name = cookie_name or "api_key"

    def auth_flow(
        self, request: httpx.Request
    ) -> ty.Generator[httpx.Request, httpx.Response, None]:
        request.headers['Cookie'] = f'{self.cookie_parameter_name}={self.api_key}'
        yield request
