from collections.abc import Collection
from typing import Optional

import mimeparse


def find_mime(supported_mimes: Optional[Collection[str]], search_mime: str) -> Optional[str]:
    if supported_mimes is None or len(supported_mimes) == 0:
        return None
    match = mimeparse.best_match(supported_mimes, search_mime)
    return match if match != '' else None
