from typing import Optional

from .mime import find_mime, MIME_JSON
from .response import ResponseMap


def get_accept_header(response_map: Optional[ResponseMap], global_response_map: Optional[ResponseMap]) -> Optional[str]:
    all_mime_types = {
        mime
        for rmap in [response_map, global_response_map]
        if rmap is not None
        for mime_map in rmap.values()
        for mime in mime_map.keys()
    }
    return find_mime(all_mime_types, MIME_JSON)
