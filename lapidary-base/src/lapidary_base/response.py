import inspect
import logging
from collections.abc import Mapping, Generator
from typing import Optional, Type, TypeVar, cast

import httpx
import pydantic

from .http_consts import CONTENT_TYPE
from .mime import find_mime

T = TypeVar('T')

MimeMap = Mapping[str, Type[T]]
ResponseMap = dict[str, MimeMap]

logger = logging.getLogger(__name__)


def _handle_response(
        response: httpx.Response,
        response_map: Optional[ResponseMap],
        global_response_map: Optional[ResponseMap],
) -> T:
    response.read()

    typ = find_type(response, response_map, global_response_map)

    if typ is None:
        response.raise_for_status()
        return response.content

    try:
        obj = parse_model(response, cast(Type[T], typ))
    except pydantic.ValidationError:
        raise ValueError(response.content)

    if isinstance(obj, Exception):
        raise obj
    else:
        return obj


def parse_model(response: httpx.Response, typ: Type[T]) -> T:
    if inspect.isclass(typ):
        if issubclass(typ, Exception):
            return typ(response.json())
        elif pydantic.BaseModel in inspect.getmro(typ):
            return typ.parse_raw(response.content)

    return pydantic.parse_raw_as(typ, response.content)


def find_type(response: httpx.Response, response_map, global_response_map) -> Optional[Type]:
    status_code = str(response.status_code)
    if CONTENT_TYPE not in response.headers:
        return None
    content_type = response.headers[CONTENT_TYPE]

    if content_type is None:
        return None

    typ = None

    if response_map:
        typ = find_type_(status_code, content_type, response_map)

    if typ is None and global_response_map is not None:
        typ = find_type_(status_code, content_type, global_response_map)

    return typ


def find_type_(code: str, mime: str, response_map: dict[str, dict[str, Type]]) -> Optional[Type]:
    for code_match in _status_code_matches(code):
        if code_match in response_map:
            mime_map = response_map[code_match]
            break
    else:
        return None

    mime_match = find_mime(mime_map.keys(), mime)
    return mime_map[mime_match] if mime_match is not None else None


def _status_code_matches(code: str) -> Generator[str, None, None]:
    yield code

    code_as_list = list(code)
    for pos in [-1, -2]:
        code_as_list[pos] = 'X'
        yield ''.join(code_as_list)

    yield 'default'
