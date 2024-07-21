from collections.abc import Collection
from typing import Optional

import mimeparse


def find_mime(supported_mimes: Optional[Collection[str]], search_mime: str) -> Optional[str]:
    if supported_mimes is None or len(supported_mimes) == 0:
        return None
    match = mimeparse.best_match(supported_mimes, search_mime)
    return match if match != '' else None


def is_json(media_type: str) -> bool:
    media_type, subtype, params = mimeparse.parse_mime_type()
    return media_type == 'application' and (subtype == 'json' or subtype.endswith('+json'))
