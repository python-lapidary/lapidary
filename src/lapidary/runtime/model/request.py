import dataclasses as dc
import inspect
from collections.abc import Iterable, Mapping

import httpx
import typing_extensions as typing

from .. import _httpx
from ..http_consts import ACCEPT
from ..types_ import SecurityRequirements
from .annotations import NameTypeAwareAnnotation, RequestContributor, find_annotation

if typing.TYPE_CHECKING:
    from ..client_base import ClientBase
    from ..operation import Operation


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

    method: str
    path: str

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


@dc.dataclass
class RequestAdapter:
    name: str
    http_method: str
    http_path_template: str
    contributors: Mapping[str, RequestContributor]
    accept: typing.Optional[Iterable[str]]
    security: typing.Optional[Iterable[SecurityRequirements]]

    def build_request(
        self,
        client: 'ClientBase',
        kwargs: dict[str, typing.Any],
    ) -> tuple[httpx.Request, typing.Optional[httpx.Auth]]:
        builder = RequestBuilder(
            typing.cast(RequestFactory, client._client.build_request),
            self.http_method,
            self.http_path_template,
        )

        for param_name, value in kwargs.items():
            self.contributors[param_name].apply_request(builder, value)

        if ACCEPT not in builder.headers and self.accept is not None:
            builder.headers.update([(ACCEPT, value) for value in self.accept])
        auth = client._auth_registry.resolve_auth(self.name, self.security)
        return builder(), auth


def prepare_request_adapter(name: str, sig: inspect.Signature, operation: 'Operation', accept: Iterable[str]) -> RequestAdapter:
    contributors = dict(process_param(param) for param in sig.parameters.values() if param.annotation != typing.Self)
    return RequestAdapter(
        name,
        operation.method,
        operation.path,
        contributors,
        accept,
        operation.security,
    )


def process_param(param: inspect.Parameter) -> tuple[str, RequestContributor]:
    name = param.name
    annotation = param.annotation

    if annotation is None:
        raise TypeError(f'{name}: Missing  type annotation')

    typ, annotation = find_annotation(annotation, RequestContributor)  # type: ignore[type-abstract]
    if isinstance(annotation, NameTypeAwareAnnotation):
        annotation.supply_formal(name, typ)
    return name, annotation
