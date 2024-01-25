import dataclasses as dc

from ..compat import typing as ty

T = ty.TypeVar('T')
MimeType = str
ResponseCode = str

MimeMap = ty.Mapping[MimeType, ty.Type]
ResponseMap = ty.Mapping[ResponseCode, MimeMap]


@dc.dataclass
class Responses:
    responses: ResponseMap
