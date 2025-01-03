import abc
import dataclasses as dc
import functools as ft
import inspect
from collections.abc import Callable, Iterable, Mapping, MutableMapping

import httpx
import mimeparse
import pydantic
import typing_extensions as typing

from ..annotations import Body, Cookie, Header, Metadata, Param, Path, Query, WebArg
from ..http_consts import ACCEPT, CONTENT_TYPE, MIME_JSON
from ..metattype import is_array_like, make_not_optional
from ..types_ import Dumper, MimeType, RequestFactory, SecurityRequirements, Signature
from .annotations import (
    find_annotation,
    find_field_annotation,
)
from .param_serialization import SCALAR_TYPES, Multimap, ScalarType

if typing.TYPE_CHECKING:
    from ..client_base import ClientBase
    from ..operation import Operation
import logging

logger = logging.getLogger(__name__)


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
    path_params: typing.MutableMapping[str, ScalarType] = dc.field(default_factory=dict)
    query_params: list[tuple[str, str]] = dc.field(default_factory=list)

    content: typing.Optional[httpx._types.RequestContent] = None

    def __call__(self) -> httpx.Request:
        assert self.method
        assert self.path

        return self.request_factory(
            self.method,
            self.path.format_map(self.path_params),
            content=self.content,
            params=httpx.QueryParams(self.query_params),
            headers=self.headers,
            cookies=self.cookies,
        )


class RequestContributor(abc.ABC):
    @abc.abstractmethod
    def update_builder(self, builder: RequestBuilder, value: typing.Any) -> None:
        pass


PST = typing.TypeVar('PST', Multimap, str)


@dc.dataclass
class ParamContributor(typing.Generic[PST], RequestContributor, abc.ABC):
    param: Param
    python_name: str
    python_type: type
    _serialize: Callable[[str, typing.Any], PST] = dc.field(init=False)

    def __post_init__(self):
        non_optional_type = make_not_optional(self.python_type)
        if non_optional_type in SCALAR_TYPES:
            self._serialize = self.param.style.serialize_scalar
        elif is_array_like(non_optional_type):
            self._serialize = self.param.style.serialize_array
        else:
            self._serialize = self.param.style.serialize

    def http_name(self) -> str:
        return self.param.alias or self.python_name


class DictParamContributor(ParamContributor, abc.ABC):
    def update_builder(self, builder: RequestBuilder, value: typing.Any) -> None:
        part = self._get_builder_part(builder)
        http_name = self.http_name()
        part.update(self._serialize(http_name, value))

    @staticmethod
    @abc.abstractmethod
    def _get_builder_part(builder: RequestBuilder) -> MutableMapping[str, str]:
        pass


class HeaderContributor(DictParamContributor):
    @staticmethod
    def _get_builder_part(builder: RequestBuilder) -> MutableMapping[str, str]:
        return builder.headers


class CookieContributor(ParamContributor):
    @staticmethod
    def _get_builder_part(builder: RequestBuilder) -> MutableMapping[str, str]:
        return builder.cookies

    def update_builder(self, builder: RequestBuilder, value: Multimap) -> None:
        for key, value in value:
            builder.cookies.set(key, value, builder.path)


class PathContributor(ParamContributor):
    def update_builder(self, builder: RequestBuilder, value: typing.Any) -> None:
        builder.path_params[self.http_name()] = self._serialize(self.http_name(), value)


class QueryContributor(ParamContributor):
    def update_builder(self, builder: RequestBuilder, value: typing.Any) -> None:
        http_name = self.http_name()
        builder.query_params.extend(self._serialize(http_name, value))


CONTRIBUTOR_MAP = {
    Path: PathContributor,
    Query: QueryContributor,
    Header: HeaderContributor,
    Cookie: CookieContributor,
}


@dc.dataclass
class ParamsContributor(RequestContributor):
    contributors: Mapping[str, RequestContributor]

    def update_builder(self, builder: RequestBuilder, headers_model: pydantic.BaseModel) -> None:
        raw_model = headers_model.model_dump(mode='json', exclude_unset=True)
        for field_name in headers_model.model_fields_set:
            assert field_name in headers_model.model_fields
            value = raw_model[field_name]
            if value is None:
                continue
            contributor = self.contributors[field_name]
            contributor.update_builder(builder, value)

    @classmethod
    def for_type(cls, model_type: type[pydantic.BaseModel]) -> typing.Self:
        contributors = {}
        for field_name, field_info in model_type.model_fields.items():
            typ, webarg = find_field_annotation(field_info, Param)
            try:
                contributor = CONTRIBUTOR_MAP[type(webarg)](webarg, field_name, typ)  # type: ignore[abstract]
            except KeyError:
                raise TypeError('Unsupported annotation', webarg)
            contributors[field_name] = contributor
        return cls(contributors=contributors)


@dc.dataclass
class FreeParamsContributor(ParamsContributor):
    model_type: type[pydantic.BaseModel]

    def update_builder(self, builder: RequestBuilder, free_params: Mapping[str, typing.Any]) -> None:
        try:
            model = self.model_type.model_validate(free_params)
        except pydantic.ValidationError as e:
            raise TypeError from e
        super().update_builder(builder, model)


@dc.dataclass
class BodyContributor:
    serializers: list[tuple[pydantic.TypeAdapter, str]]

    def update_builder(self, builder: 'RequestBuilder', value: typing.Any, media_type: MimeType = MIME_JSON) -> None:
        matched_media_type, content = self._dump(value, media_type)
        builder.headers[CONTENT_TYPE] = matched_media_type
        builder.content = content

    def _dump(self, value: typing.Any, media_type: MimeType = MIME_JSON):
        for type_adapter, media_type_ in self.serializers:
            if not BodyContributor._media_matches(media_type_, media_type):
                logger.debug('Ignoring unsupported media_type: %s', media_type)
                continue
            try:
                raw = type_adapter.dump_json(value, exclude_unset=True, by_alias=True)
                return media_type_, raw
            except pydantic.ValidationError:
                continue
        else:
            raise ValueError('Unsupported value')

    @classmethod
    def for_parameter(cls, annotation: type) -> typing.Self:
        body: Body
        _, body = find_annotation(annotation, Body)
        serializers = [
            (pydantic.TypeAdapter(python_type), media_type)
            for media_type, python_type in body.content.items()
            if BodyContributor._media_matches(media_type)
        ]
        return cls(serializers)

    @staticmethod
    def _media_matches(media_type: str, match: str = MIME_JSON) -> bool:
        m_type, m_subtype, _ = mimeparse.parse_media_range(media_type)
        return f'{m_type}/{m_subtype}' == match


@dc.dataclass
class RequestObjectContributor(RequestContributor):
    contributors: Mapping[str, RequestContributor]  # keys are params names

    body_param: typing.Optional[str]
    body_contributor: typing.Optional[BodyContributor]

    free_param_contributor: typing.Optional[FreeParamsContributor]
    free_param_names: Iterable[str]

    def update_builder(self, builder: RequestBuilder, kwargs: dict[str, typing.Any]) -> None:
        free_params: dict[str, typing.Any] = {}
        for name, value in kwargs.items():
            if name == self.body_param:
                assert self.body_contributor is not None
                self.body_contributor.update_builder(builder, value)
            elif name in self.free_param_names:
                free_params[name] = value
            else:
                try:
                    contributor = self.contributors[name]
                except KeyError:
                    raise TypeError('Unexpected argument', name) from None
                contributor.update_builder(builder, value)
        if self.free_param_contributor:
            self.free_param_contributor.update_builder(builder, free_params)

    @classmethod
    def for_signature(cls, sig: Signature) -> typing.Self:
        contributors: dict[str, RequestContributor] = {}
        body_param: typing.Optional[str] = None
        body_contributor: typing.Optional[BodyContributor] = None

        free_params: dict[str, typing.Any] = {}  # python name => annotation

        for param in sig.values():
            if param.annotation is typing.Self:
                continue

            typ, web_arg = find_annotation(param.annotation, WebArg)

            if type(web_arg) in CONTRIBUTOR_MAP:
                default = ... if param.default is inspect.Parameter.empty else param.default
                free_params[param.name] = param.annotation, typ, web_arg, default
            elif isinstance(web_arg, Body):
                body_param = param.name
                body_contributor = BodyContributor.for_parameter(param.annotation)
            elif isinstance(web_arg, Metadata):
                contributors[param.name] = ParamsContributor.for_type(typing.cast(type[pydantic.BaseModel], typ))
            else:
                raise TypeError('Unsupported annotation', web_arg)

        free_param_contributor, free_param_names = cls._mk_free_params_contributor(free_params)

        return cls(
            contributors=contributors,
            body_param=body_param,
            body_contributor=body_contributor,
            free_param_contributor=free_param_contributor,
            free_param_names=free_param_names,
        )

    @staticmethod
    def _mk_free_params_contributor(free_params: Mapping[str, typing.Any]) -> tuple[typing.Optional[FreeParamsContributor], Iterable[str]]:
        if not free_params:
            return None, set()

        model_fields = {}
        contributors = {}
        for python_name, anno_tuple in free_params.items():
            annotation, typ, web_arg, default = anno_tuple
            model_fields[python_name] = (annotation, default)
            contributors[python_name] = CONTRIBUTOR_MAP[type(web_arg)](web_arg, python_name, typ)  # type: ignore[abstract,index,arg-type]
        model_type = pydantic.create_model('$name', **model_fields)
        free_param_contributor = FreeParamsContributor(contributors=contributors, model_type=model_type)
        return free_param_contributor, set(model_fields.keys())


@dc.dataclass
class RequestAdapter:
    name: str
    http_method: str
    http_path_template: str
    contributor: RequestContributor
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

        self.contributor.update_builder(builder, kwargs)

        accept_values: set[str] = set()
        if ACCEPT not in builder.headers and self.accept is not None:
            accept_values |= set(self.accept)
        builder.headers.update([(ACCEPT, value) for value in accept_values])
        auth = client._auth_registry.resolve_auth(self.name, self.security)
        return builder(), auth


def prepare_request_adapter(name: str, sig: Signature, operation: 'Operation', accept: Iterable[str]) -> RequestAdapter:
    return RequestAdapter(
        name,
        operation.method,
        operation.path,
        RequestObjectContributor.for_signature(sig),
        accept,
        operation.security,
    )


@dc.dataclass
class PydanticDumper(Dumper):
    _type_adapter: pydantic.TypeAdapter

    def __call__(self, value: typing.Any) -> bytes:
        return self._type_adapter.dump_json(value, by_alias=True, exclude_defaults=True)


@ft.cache
def mk_pydantic_dumper(typ: type) -> Dumper:
    return PydanticDumper(pydantic.TypeAdapter(typ))
