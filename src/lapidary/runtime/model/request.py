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
from ..mime import find_mime
from ..types_ import Dumper, MimeType, RequestFactory, SecurityRequirements
from .annotations import (
    find_annotation,
    find_field_annotation,
)
from .encode_param import Encoder, get_encode_fn

if typing.TYPE_CHECKING:
    from ..client_base import ClientBase
    from ..operation import Operation


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


class RequestContributor(abc.ABC):
    @abc.abstractmethod
    def update_builder(self, builder: RequestBuilder, value: typing.Any) -> None:
        pass


@dc.dataclass
class ParamContributor(RequestContributor, abc.ABC):
    param: Param
    python_name: str
    python_type: type
    encode: Encoder = dc.field(init=False)

    def __post_init__(self) -> None:
        encode = get_encode_fn(self.python_type, self.param.style, self.param.explode)
        if not encode:
            raise TypeError(f'Unsupported encoding for {self.param}, style={self.param.style}, explode={self.param.explode}')
        self.encode = encode
        # TODO we need to determine the raw type or base the encoder resolution on actual type
        #  and move it to update_builder

    def http_name(self) -> str:
        return self.param.alias or self.python_name


class DictParamContributor(ParamContributor):
    def update_builder(self, builder: RequestBuilder, value: typing.Any) -> None:
        part = self._get_builder_part(builder)
        http_name = self.http_name()
        part[http_name] = self.encode(http_name, value)

    @staticmethod
    @abc.abstractmethod
    def _get_builder_part(builder: RequestBuilder) -> MutableMapping[str, str]:
        pass


class HeaderContributor(DictParamContributor):
    @staticmethod
    def _get_builder_part(builder: RequestBuilder) -> MutableMapping[str, str]:
        return builder.headers


class CookieContributor(DictParamContributor):
    @staticmethod
    def _get_builder_part(builder: RequestBuilder) -> MutableMapping[str, str]:
        return builder.cookies


class PathContributor(DictParamContributor):
    @staticmethod
    def _get_builder_part(builder: RequestBuilder) -> MutableMapping[str, str]:
        return builder.path_params


class QueryContributor(ParamContributor):
    def update_builder(self, builder: RequestBuilder, value: typing.Any) -> None:
        http_name = self.http_name()
        builder.query_params.append((http_name, self.encode(http_name, value)))


CONTRIBUTOR_MAP = {
    Path: PathContributor,
    Query: QueryContributor,
    Header: HeaderContributor,
    Cookie: CookieContributor,
}


@dc.dataclass
class ParamsContributor(RequestContributor):
    contributors: Mapping[str, RequestContributor]
    type_adapter: Callable[[pydantic.BaseModel], dict]

    def update_builder(self, builder: RequestBuilder, headers_model: pydantic.BaseModel) -> None:
        raw_model = self.type_adapter(headers_model)
        for field_name, field_info in headers_model.model_fields.items():
            value = raw_model[field_name]
            if not value and field_name not in headers_model.model_fields_set:
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
        return cls(contributors=contributors, type_adapter=pydantic.TypeAdapter(model_type).dump_python)


@dc.dataclass
class BodyContributor:
    dumpers: Mapping[type, Mapping[MimeType, Dumper]]

    def update_builder(self, builder: 'RequestBuilder', value: typing.Any, media_type: MimeType = MIME_JSON) -> None:
        matched_media_type, dump = self.find_dumper(type(value), media_type)
        builder.headers[CONTENT_TYPE] = matched_media_type
        builder.content = dump(value)

    def find_dumper(self, typ: type, media_type: MimeType) -> tuple[MimeType, Dumper]:
        for base in typ.__mro__[:-1]:
            try:
                media_dumpers = self.dumpers[base]
                matched_media_type = find_mime(media_dumpers.keys(), media_type)
                if not matched_media_type:
                    raise ValueError('Unsupported media_type', media_type)
                return matched_media_type, media_dumpers[matched_media_type]
            except KeyError:
                continue
        raise TypeError(f'Unsupported type: {typ.__name__}')

    @classmethod
    def for_parameter(cls, annotation: type) -> typing.Self:
        dumpers: dict[type, dict[MimeType, Dumper]] = {}
        body: Body
        _, body = find_annotation(annotation, Body)
        for media_type, typ in body.content.items():
            m_type, m_subtype, _ = mimeparse.parse_media_range(media_type)
            if f'{m_type}/{m_subtype}' != MIME_JSON:
                raise TypeError(f'Unsupported media type: {media_type}')
            type_dumpers = dumpers.setdefault(typ, {})
            type_dumpers[media_type] = mk_pydantic_dumper(typ)
        return cls(dumpers=dumpers)


@dc.dataclass
class RequestObjectContributor(RequestContributor):
    contributors: Mapping[str, RequestContributor]  # keys are params names

    body_param: typing.Optional[str]
    body_contributor: typing.Optional[BodyContributor]

    def update_builder(self, builder: RequestBuilder, kwargs: dict[str, typing.Any]) -> None:
        for name, value in kwargs.items():
            if name == self.body_param:
                assert self.body_contributor is not None
                self.body_contributor.update_builder(builder, value)
            else:
                try:
                    contributor = self.contributors[name]
                except KeyError:
                    raise TypeError('Unexpected argument', name)
                contributor.update_builder(builder, value)

    @classmethod
    def for_signature(cls, sig: inspect.Signature) -> typing.Self:
        contributors: dict[str, RequestContributor] = {}
        body_param: typing.Optional[str] = None
        body_contributor: typing.Optional[BodyContributor] = None
        for param in sig.parameters.values():
            if param.annotation is typing.Self:
                continue

            typ, annotation = find_annotation(param.annotation, WebArg)

            if type(annotation) in CONTRIBUTOR_MAP:
                contributors[param.name] = CONTRIBUTOR_MAP[type(annotation)](annotation, param.name, typ)  # type: ignore[abstract,index,arg-type]
            elif isinstance(annotation, Body):
                body_param = param.name
                body_contributor = BodyContributor.for_parameter(param.annotation)
            elif isinstance(annotation, Metadata):
                contributors[param.name] = ParamsContributor.for_type(typing.cast(type[pydantic.BaseModel], typ))
            else:
                raise TypeError('Unsupported annotation', annotation)

        return cls(contributors=contributors, body_param=body_param, body_contributor=body_contributor)


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

        if ACCEPT not in builder.headers and self.accept is not None:
            builder.headers.update([(ACCEPT, value) for value in self.accept])
        auth = client._auth_registry.resolve_auth(self.name, self.security)
        return builder(), auth


def prepare_request_adapter(name: str, sig: inspect.Signature, operation: 'Operation', accept: Iterable[str]) -> RequestAdapter:
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
        return self._type_adapter.dump_json(value)


@ft.cache
def mk_pydantic_dumper(typ: type) -> Dumper:
    return PydanticDumper(pydantic.TypeAdapter(typ))
