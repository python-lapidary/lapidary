import dataclasses as dc

import httpx
import typing_extensions as typing


class RequestFactory(typing.Protocol):
    """Protocol for httpx.BaseClient.build_request()"""

    def __call__(  # pylint: disable=too-many-arguments
        self,
        method: str,
        url: str,
        *,
        content: typing.Optional[httpx._types.RequestContent] = None,
        # data: typing.Optional[httpx._types.RequestData] = None,
        # files: typing.Optional[httpx._types.RequestFiles] = None,
        # json: typing.Optional[typing.Any] = None,
        params: typing.Optional[httpx._types.QueryParamTypes] = None,
        headers: typing.Optional[httpx._types.HeaderTypes] = None,
        cookies: typing.Optional[httpx._types.CookieTypes] = None,
        # timeout: typing.Union[httpx._types.TimeoutTypes, httpx._client.UseClientDefault] = httpx.USE_CLIENT_DEFAULT,
        # extensions: typing.Optional[httpx._types.RequestExtensions] = None,
    ) -> httpx.Request:
        pass


@dc.dataclass
class RequestBuilder:  # pylint: disable=too-many-instance-attributes
    """
    Class for incremental building requests. A holder for all required parameters of AsyncClient.send().
    Can be used like a mutable version of httpx.Request, extended with path parameters and auth.
    """

    request_factory: RequestFactory

    method: str
    path: str

    cookies: httpx.Cookies = dc.field(default_factory=httpx.Cookies)
    headers: httpx.Headers = dc.field(default_factory=httpx.Headers)
    path_params: typing.MutableMapping[str, httpx._types.PrimitiveData] = dc.field(default_factory=dict)
    query_params: typing.MutableMapping[str, str] = dc.field(default_factory=dict)

    content: typing.Optional[httpx._types.RequestContent] = None
    auth: typing.Optional[httpx.Auth] = None

    def __call__(self) -> tuple[httpx.Request, typing.Optional[httpx.Auth]]:
        return (
            self.request_factory(
                self.method,
                self.path.format_map(self.path_params),
                content=self.content,
                params=httpx.QueryParams(self.query_params),
                headers=self.headers,
                cookies=self.cookies,
            ),
            self.auth,
        )
