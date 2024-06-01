import inspect

import httpx
import typing_extensions as typing

from .http_consts import ACCEPT, MIME_JSON
from .mime import find_mime
from .model.annotations import NameTypeAwareAnnotation, ResponseMap, find_annotations
from .model.op import OperationModel
from .model.request import RequestBuilder, RequestFactory


def get_accept_header(response_map: typing.Optional[ResponseMap]) -> typing.Optional[str]:
    if not response_map:
        return None

    all_mime_types = {mime for mime_map in response_map.values() for mime in mime_map.keys()}
    return find_mime(all_mime_types, MIME_JSON)


def build_request(
    operation: 'OperationModel',
    actual_params: typing.Mapping[str, typing.Any],
    request_factory: RequestFactory,
) -> httpx.Request:
    builder = RequestBuilder(
        request_factory,
        operation.method,
        operation.path,
    )
    operation.process_params(actual_params, builder)

    if ACCEPT not in builder.headers and (accept := get_accept_header(operation.response_map)) is not None:
        builder.headers[ACCEPT] = accept

    return builder()


def process_params(sig: inspect.Signature) -> typing.Mapping[str, NameTypeAwareAnnotation]:
    return dict(process_param(param) for param in sig.parameters.values() if param.annotation not in (typing.Self, None))


def process_param(param: inspect.Parameter) -> typing.Tuple[str, NameTypeAwareAnnotation]:
    name = param.name
    typ = param.annotation

    annotations = find_annotations(typ, NameTypeAwareAnnotation)  # type: ignore[type-abstract]
    if len(annotations) != 1:
        raise ValueError(f'{name}: expected exactly one Lapidary annotation.', typ)
    annotation = annotations[0]
    annotation.supply_formal(name, typ.__origin__)
    return name, annotation
