import inspect
import logging
from typing import Any, AsyncIterator, Iterable, Iterator, Optional, Type, TypeVar, cast

import httpx
import pydantic

from .http_consts import CONTENT_TYPE
from .mime import find_mime
from .model import ResponseMap
from .model.response_map import ReturnTypeInfo

logger = logging.getLogger(__name__)

T = TypeVar('T')
P = TypeVar('P')


def handle_response(
        response_map: ResponseMap,
        response: httpx.Response,
) -> Any:
    response.read()

    type_info = find_type(response, response_map)

    if type_info is None:
        response.raise_for_status()
        return response.content

    try:
        obj: Any = parse_model(response, type_info.type)
    except pydantic.ValidationError as error:
        raise ValueError(response.content) from error

    if isinstance(obj, Exception):
        raise obj
    elif type_info.iterator:
        return aiter2(obj)
    else:
        return obj


async def aiter2(values: Iterable[T]) -> AsyncIterator[T]:
    """Turn Iterable to AsyncIterator (AsyncGenerator really)."""
    for value in values:
        yield value


def parse_model(response: httpx.Response, typ: Type[T]) -> T:
    if inspect.isclass(typ):
        if issubclass(typ, Exception):
            return typ(response.json())  # type: ignore[return-value]
        elif pydantic.BaseModel in inspect.getmro(typ):
            return cast(Type[pydantic.BaseModel], typ).model_validate_json(response.content)

    return pydantic.TypeAdapter(typ).validate_json(response.content)


def find_type(response: httpx.Response, response_map: ResponseMap) -> Optional[ReturnTypeInfo]:
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


def find_type_(code: str, mime: str, response_map: ResponseMap) -> Optional[ReturnTypeInfo]:
    for code_match in _status_code_matches(code):
        if code_match in response_map:
            mime_map = response_map[code_match]
            break
    else:
        return None

    mime_match = find_mime(mime_map.keys(), mime)
    return mime_map[mime_match] if mime_match is not None else None


def _status_code_matches(code: str) -> Iterator[str]:
    yield code
    yield code[0] + "XX"
    yield 'default'
