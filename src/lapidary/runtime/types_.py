from collections.abc import Mapping, MutableMapping

import httpx
import httpx_auth
import pydantic
import typing_extensions as typing

MultiAuth: typing.TypeAlias = httpx_auth._authentication._MultiAuth  # pylint: disable=protected-access
NamedAuth: typing.TypeAlias = tuple[str, httpx.Auth]
SecurityRequirements: typing.TypeAlias = typing.Mapping[str, typing.Iterable[str]]

HeadersModel = typing.TypeVar('HeadersModel', bound=pydantic.BaseModel)
BodyModel = typing.TypeVar('BodyModel', bound=pydantic.BaseModel)
MimeType: typing.TypeAlias = str
ResponseCode: typing.TypeAlias = str
MimeMap: typing.TypeAlias = MutableMapping[MimeType, type]
ResponseMap: typing.TypeAlias = Mapping[ResponseCode, MimeMap]
