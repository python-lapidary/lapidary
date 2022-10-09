import typing
from typing import Optional, Type, Generator, TypeVar, cast

import httpx
import pydantic

from .mime import find_mime

T = TypeVar('T')

MimeMap = typing.Mapping[str, Type[T]]
ResponseMap = dict[str, MimeMap]


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

    obj = parse_model(response, cast(Type[T], typ))

    if isinstance(obj, Exception):
        raise obj
    else:
        return obj


def parse_model(response: httpx.Response, typ: Type[T]) -> T:
    if hasattr(typ, 'mro'):
        if Exception in typ.mro():
            return typ(response.json())
        elif pydantic.BaseModel in typ.mro():
            return typ.parse_raw(response.content)

    return pydantic.parse_raw_as(typ, response.content)


def find_type(response: httpx.Response, response_map, global_response_map) -> Optional[Type]:
    status_code = str(response.status_code)
    content_type = response.headers.get('content-type', None)

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
