from typing import Any

import pydantic
from pydantic.tools import _get_parsing_type


def to_model(request_body: Any) -> pydantic.BaseModel:
    model_type = _get_parsing_type(type(request_body))
    request_body = model_type(__root__=request_body)
    return request_body
