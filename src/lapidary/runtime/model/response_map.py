import dataclasses as dc

import typing_extensions as typing

T = typing.TypeVar('T')
MimeType = str
ResponseCode = str

MimeMap = typing.Mapping[MimeType, typing.Type]
ResponseMap = typing.Mapping[ResponseCode, MimeMap]


@dc.dataclass
class Responses:
    responses: ResponseMap
