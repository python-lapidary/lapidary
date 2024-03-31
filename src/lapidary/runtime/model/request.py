import dataclasses as dc

import httpx
import typing_extensions as typing

from .. import _httpx


class RequestFactory(typing.Protocol):
    """Protocol for httpx.BaseClient.build_request()"""

    def __call__(  # pylint: disable=too-many-arguments
        self,
        method: str,
        url: str,
        *,
        content: typing.Optional[httpx._types.RequestContent] = None,
        _data: typing.Optional[httpx._types.RequestData] = None,
        _files: typing.Optional[httpx._types.RequestFiles] = None,
        _json: typing.Optional[typing.Any] = None,
        params: typing.Optional[httpx._types.QueryParamTypes] = None,
        headers: typing.Optional[httpx._types.HeaderTypes] = None,
        cookies: typing.Optional[httpx._types.CookieTypes] = None,
        _timeout: typing.Union[httpx._types.TimeoutTypes, _httpx.UseClientDefault] = httpx.USE_CLIENT_DEFAULT,
        _extensions: typing.Optional[httpx._types.RequestExtensions] = None,
    ) -> httpx.Request:
        pass


@dc.dataclass
class RequestBuilder:  # pylint: disable=too-many-instance-attributes
    """
    Class for incremental building requests. A holder for all required parameters of AsyncClient.send().
    Can be used like a mutable version of httpx.Request, extended with path parameters.
    """

    request_factory: RequestFactory

    method: typing.Optional[str] = None
    path: typing.Optional[str] = None

    cookies: httpx.Cookies = dc.field(default_factory=httpx.Cookies)
    headers: httpx.Headers = dc.field(default_factory=httpx.Headers)
    path_params: typing.MutableMapping[str, httpx._types.PrimitiveData] = dc.field(default_factory=dict)
    query_params: typing.MutableSequence[tuple[str, str]] = dc.field(default_factory=list)

    content: typing.Optional[httpx._types.RequestContent] = None

    def __call__(self) -> httpx.Request:
        assert self.method
        assert self.path

        return self.request_factory(
            self.method,
            self.path.format_map(self.path_params),
            content=self.content,
            params=httpx.QueryParams(tuple(self.query_params)),
            headers=self.headers,
            cookies=self.cookies,
        )
