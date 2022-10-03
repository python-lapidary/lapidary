from typing import Optional, Type, Iterable, Generator, TypeVar

import httpx
import pydantic

T = TypeVar('T')


def _handle_response(response: httpx.Response, response_mapping: Optional[dict[str, dict[str, Type[T]]]] = None) -> T:
    if response_mapping:
        response_obj = resolve_response(response, response_mapping)
        if isinstance(response_obj, Exception):
            raise response_obj
        else:
            return response_obj
    else:
        response.raise_for_status()
        return response.json()


def resolve_response(response: httpx.Response, mapping: dict[str, dict[str, Type[T]]]) -> T:
    code_match = find_code_mapping(str(response.status_code), mapping)
    data = response.json()

    if code_match is None:
        response.raise_for_status()
        return data

    mime_mapping = mapping[code_match]
    mime_match = find_mime(mime_mapping.keys(), response.headers['content-type'])

    if mime_match is not None:
        typ = mime_mapping[mime_match]

        if hasattr(typ, 'mro') and Exception in typ.mro():
            return typ(data)

        try:
            return pydantic.parse_obj_as(typ, data)
        except pydantic.ValidationError:
            raise ValueError('Error parsing response as type', typ)

    else:
        response.raise_for_status()
        return data


def find_code_mapping(code: str, mapping: dict[str, dict[str, Type]]) -> Optional[str]:
    for code_match in _status_code_matches(code):
        if code_match in mapping:
            return code_match
    else:
        return None


def find_mime(supported_mimes: Iterable[str], response_mime: str) -> str:
    from mimeparse import best_match
    match = best_match(supported_mimes, response_mime)
    return match if match != '' else None


def _status_code_matches(code: str) -> Generator[str, None, None]:
    yield code

    code_as_list = list(code)
    for pos in [-1, -2]:
        code_as_list[pos] = 'X'
        yield ''.join(code_as_list)

    yield 'default'
