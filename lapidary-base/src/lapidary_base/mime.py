from typing import Iterable, Optional
from mimeparse import best_match

MIME_JSON = 'application/json'


def find_mime(supported_mimes: Optional[Iterable[str]], search_mime: str) -> Optional[str]:
    if supported_mimes is None or len(supported_mimes) == 0:
        return None
    match = best_match(supported_mimes, search_mime)
    return match if match != '' else None
