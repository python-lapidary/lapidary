from typing import Any

import pydantic


def to_model(request_body: Any) -> pydantic.BaseModel:
    from pydantic.tools import _get_parsing_type
    model_type = _get_parsing_type(type(request_body))
    request_body = model_type(__root__=request_body)
    return request_body
