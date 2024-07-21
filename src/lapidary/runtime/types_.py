import abc
from collections.abc import MutableMapping

import httpx
import httpx_auth
import pydantic
import typing_extensions as typing

from . import _httpx

MultiAuth: typing.TypeAlias = httpx_auth._authentication._MultiAuth  # pylint: disable=protected-access
NamedAuth: typing.TypeAlias = tuple[str, httpx.Auth]
SecurityRequirements: typing.TypeAlias = typing.Mapping[str, typing.Iterable[str]]

HeadersModel = typing.TypeVar('HeadersModel', bound=pydantic.BaseModel)
BodyModel = typing.TypeVar('BodyModel', bound=pydantic.BaseModel)
MimeType: typing.TypeAlias = str
ResponseCode: typing.TypeAlias = str
MimeMap: typing.TypeAlias = MutableMapping[MimeType, type]


class Dumper(abc.ABC):
    @abc.abstractmethod
    def __call__(self, obj: typing.Any) -> bytes:
        pass


class Parser(abc.ABC):
    @abc.abstractmethod
    def __call__(self, raw: bytes) -> typing.Any:
        pass


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
