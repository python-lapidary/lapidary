import inspect
import logging

import httpx
import pydantic
import typing_extensions as typing

from .http_consts import CONTENT_TYPE
from .mime import find_mime
from .model.response_map import ResponseMap

logger = logging.getLogger(__name__)

T = typing.TypeVar('T')
P = typing.TypeVar('P')


def parse_model(response: httpx.Response, typ: type[T]) -> T:
    if inspect.isclass(typ):
        if issubclass(typ, pydantic.BaseModel):
            return typing.cast(T, typ.model_validate_json(response.content))

    return pydantic.TypeAdapter(typ).validate_json(response.content)


def find_type(response: httpx.Response, response_map: ResponseMap) -> typing.Optional[type]:
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


def find_type_(code: str, mime: str, response_map: ResponseMap) -> typing.Optional[type]:
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
