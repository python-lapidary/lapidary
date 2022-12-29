import inspect
import logging
from collections.abc import Iterator, AsyncIterator, Iterable, AsyncGenerator
from typing import Optional, Type, TypeVar, Callable, Any

import httpx
import pydantic

from .http_consts import CONTENT_TYPE
from .mime import find_mime
from .model import ResponseMap, PagingPlugin
from .model.response_map import ReturnTypeInfo

logger = logging.getLogger(__name__)

T = TypeVar('T')
P = TypeVar('P')


def handle_response(
        response_map: Optional[ResponseMap],
        global_response_map: Optional[ResponseMap],
        response: httpx.Response,
) -> Any:
    response.read()

    type_info = find_type(response, response_map, global_response_map)

    if type_info is None:
        response.raise_for_status()
        return response.content

    type_, iterator = type_info

    try:
        obj = parse_model(response, type_)
    except pydantic.ValidationError:
        raise ValueError(response.content)

    if isinstance(obj, Exception):
        raise obj
    elif iterator:
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
            return typ(response.json())
        elif pydantic.BaseModel in inspect.getmro(typ):
            return typ.parse_raw(response.content)

    return pydantic.parse_raw_as(typ, response.content)


def find_type(response: httpx.Response, response_map: ResponseMap, global_response_map: ResponseMap) -> Optional[ReturnTypeInfo]:
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

    code_as_list = list(code)
    for pos in [-1, -2]:
        code_as_list[pos] = 'X'
        yield ''.join(code_as_list)

    yield 'default'


async def mk_generator(
        paging: PagingPlugin[T, P], request: httpx.Request, auth: Optional[httpx.Auth], client: httpx.AsyncClient,
        response_handler: Callable[[httpx.Response], T]
) -> AsyncIterator[P]:
    async for response in get_pages(paging, request, auth, client):
        response_model = response_handler(response)
        processed = paging.map_response(response_model)

        if isinstance(processed, AsyncIterator):
            async for elem in processed:
                yield elem
        else:
            yield processed


async def get_pages(
        paging: PagingPlugin, request: httpx.Request, auth: Optional[httpx.Auth], client: httpx.AsyncClient
) -> AsyncGenerator[httpx.Response, None]:
    flow = paging.page_flow(request)
    request = next(flow)
    while True:
        response = await client.send(request, auth=auth)
        yield response
        try:
            request = flow.send(response)
        except StopIteration:
            break
