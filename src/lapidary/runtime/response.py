import pydantic
import typing_extensions as typing

from .annotations import StatusCode


class ResponseHeaders(pydantic.BaseModel):
    status_code: typing.Annotated[int, StatusCode]
