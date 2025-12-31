from collections.abc import Collection

import mimeparse


def find_mime(supported_mimes: Collection[str] | None, search_mime: str) -> str | None:
    if supported_mimes is None or len(supported_mimes) == 0:
        return None
    match = mimeparse.best_match(supported_mimes, search_mime)
    return match if match != '' else None
