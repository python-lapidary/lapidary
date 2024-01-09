import dataclasses as dc

from ..compat import typing as ty

T = ty.TypeVar('T')
MimeType = str
ResponseCode = str


@dc.dataclass
class ReturnTypeInfo:
    type: ty.Type
    iterator: bool = False


MimeMap = ty.Mapping[MimeType, ReturnTypeInfo]
ResponseMap = ty.Mapping[ResponseCode, MimeMap]


@dc.dataclass(frozen=True)
class Responses:
    responses: ResponseMap

    def get_response(self, response_code: int, mime_type: str) -> ReturnTypeInfo:
        pass
