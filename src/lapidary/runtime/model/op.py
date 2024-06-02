import inspect
from collections.abc import Awaitable, Callable, Iterable, Mapping, MutableMapping

import httpx
import pydantic.fields
import typing_extensions as typing

from .. import ResponseEnvelope
from ..http_consts import ACCEPT, CONTENT_TYPE, MIME_JSON
from ..mime import find_mime
from ..types_ import SecurityRequirements
from .annotations import NameTypeAwareAnnotation, ResponseBody, Responses, find_annotations
from .request import RequestBuilder, RequestFactory, RequestHandler
from .response import ResponseHandler

if typing.TYPE_CHECKING:
    from ..client_base import ClientBase

ResponseHandlerMap: typing.TypeAlias = Mapping[str, Mapping[str, tuple[type[ResponseEnvelope], Iterable[ResponseHandler]]]]
ResponseHandlerMapMut: typing.TypeAlias = MutableMapping[str, MutableMapping[str, tuple[type[ResponseEnvelope], Iterable[ResponseHandler]]]]


class OperationModel:
    method: str
    path: str
    params: typing.Mapping[str, RequestHandler]
    response_handler_map: ResponseHandlerMap
    security: typing.Optional[Iterable[SecurityRequirements]]
    name: str

    def __init__(
        self,
        method: str,
        path: str,
        security: typing.Optional[Iterable[SecurityRequirements]],
        fn: Callable[..., Awaitable[typing.Any]],
    ):
        self.method = method
        self.path = path
        self.security = security

        self.name = fn.__name__

        sig = inspect.signature(fn)
        try:
            self.params = process_params(sig)
            self.response_handler_map = get_response_map(sig.return_annotation)
        except TypeError as error:
            raise TypeError(fn.__name__) from error

    async def __call__(
        self,
        client: 'ClientBase',
        **actual_params: typing.Mapping[str, typing.Any],
    ) -> typing.Any:
        request = self._prepare_request(client, actual_params)
        auth = client._auth_registry.resolve_auth(self.name, self.security)

        response = await client._client.send(request, auth=auth)

        return await self.handle_response(response)

    def _prepare_request(self, client, actual_params):
        builder = RequestBuilder(
            typing.cast(RequestFactory, client._client.build_request),
            self.method,
            self.path,
        )

        for param_name, value in actual_params.items():
            param_handler = self.params[param_name]
            if isinstance(param_handler, RequestHandler):
                param_handler.apply_request(builder, actual_params[param_name])
            else:
                raise TypeError(param_name, type(value))

        if ACCEPT not in builder.headers and (accept := get_accept_header(self.response_handler_map)) is not None:
            builder.headers[ACCEPT] = accept
        return builder()

    async def handle_response(self, response: httpx.Response) -> typing.Any:
        """
        Possible special cases:
        Exception
        """

        await response.aread()
        type_handlers = find_type(response, self.response_handler_map)
        if type_handlers is None:
            return None

        typ, handlers = type_handlers

        fields: typing.MutableMapping[str, typing.Any] = {}
        for handler in handlers:
            handler.apply_response(response, fields)
        envelope: ResponseEnvelope = typ.parse_obj(fields)

        if isinstance(envelope, DefaultEnvelope):
            if isinstance(envelope.body, Exception):
                raise envelope.body
            return envelope.body
        else:
            return envelope


BodyT = typing.TypeVar('BodyT')


class DefaultEnvelope(ResponseEnvelope, typing.Generic[BodyT]):
    body: typing.Annotated[BodyT, ResponseBody]


def get_response_map(return_anno: type) -> ResponseHandlerMap:
    annos: typing.Sequence[Responses] = find_annotations(return_anno, Responses)
    if len(annos) != 1:
        raise TypeError('Operation function must have exactly one Responses annotation')

    responses = annos[0].responses
    handler_map: ResponseHandlerMapMut = {}
    for status_code, media_type_map in responses.items():
        media_type_handlers_map = {}
        for media_type, typ in media_type_map.items():
            if issubclass(typ, ResponseEnvelope):
                response_type = typ
            else:
                response_type = DefaultEnvelope[typ]  # type: ignore[valid-type]
            media_type_handlers_map[media_type] = response_type, process_response_envelope(response_type)
        handler_map[status_code] = media_type_handlers_map

    return handler_map


def process_params(sig: inspect.Signature) -> typing.Mapping[str, RequestHandler]:
    return dict(process_param(param) for param in sig.parameters.values() if param.annotation != typing.Self)


def process_param(param: inspect.Parameter) -> typing.Tuple[str, RequestHandler]:
    name = param.name
    typ = param.annotation

    if typ is None:
        raise TypeError(f'{name}: Missing  type annotation')

    annotations = find_annotations(typ, RequestHandler)  # type: ignore[type-abstract]
    if len(annotations) != 1:
        raise TypeError(f'{name}: expected exactly one Lapidary annotation.')
    annotation = annotations[0]
    if isinstance(annotation, NameTypeAwareAnnotation):
        annotation.supply_formal(name, typ.__origin__)
    return name, annotation


def get_accept_header(response_map: ResponseHandlerMap) -> typing.Optional[str]:
    if not response_map:
        return None

    all_mime_types = {mime for mime_map in response_map.values() for mime in mime_map.keys()}
    return find_mime(all_mime_types, MIME_JSON)


def process_response_envelope(typ: type[ResponseEnvelope]) -> Iterable[ResponseHandler]:
    return [process_response_field(name, field) for name, field in typ.model_fields.items()]


def process_response_field(name: str, field: pydantic.fields.FieldInfo) -> ResponseHandler:
    field_handlers = []
    for anno in field.metadata:
        if inspect.isclass(anno) and issubclass(anno, ResponseHandler):
            field_handlers.append(anno())
        elif isinstance(anno, ResponseHandler):
            field_handlers.append(anno)
    if len(field_handlers) != 1:
        raise TypeError(f'{name}: Expected exactly one ResponseHandler annotation')
    handler = field_handlers[0]

    if isinstance(handler, NameTypeAwareAnnotation):
        field_type = field.annotation
        assert field_type
        handler.supply_formal(name, field_type)
    return handler


def find_type(
    response: httpx.Response,
    response_map: 'ResponseHandlerMap',
) -> typing.Optional[tuple[type[ResponseEnvelope], Iterable[ResponseHandler]]]:
    status_code = str(response.status_code)
    if CONTENT_TYPE not in response.headers:
        return None
    content_type = response.headers[CONTENT_TYPE]

    if content_type is None:
        return None

    typ = None

    if response_map:
        typ = find_type_(status_code, content_type, response_map)

    return typ


def find_type_(code: str, mime: str, response_map: 'ResponseHandlerMap') -> typing.Optional[tuple[type, Iterable[ResponseHandler]]]:
    for code_match in _status_code_matches(code):
        if code_match in response_map:
            mime_map = response_map[code_match]
            break
    else:
        return None

    mime_match = find_mime(mime_map.keys(), mime)
    return mime_map[mime_match] if mime_match is not None else None


def _status_code_matches(code: str) -> typing.Iterator[str]:
    yield code
    yield code[0] + 'XX'
    yield 'default'
