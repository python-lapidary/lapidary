import abc
import dataclasses as dc
from collections.abc import Callable

import httpx
import pydantic
import typing_extensions as typing

T = typing.TypeVar('T')
MimeType = str
ResponseCode = str

MimeMap = typing.MutableMapping[MimeType, type]
ResponseMap = typing.Mapping[ResponseCode, MimeMap]


@dc.dataclass
class Responses:
    responses: ResponseMap


class ResponseEnvelopeBuilder:
    def __init__(self, typ: type[pydantic.BaseModel]) -> None:
        self._type = typ
        self.fields: typing.MutableMapping[str, typing.Any] = {}

    def build(self) -> typing.Any:
        return self._type.model_construct(**self.fields)


class ResponsePartHandler(abc.ABC):
    @abc.abstractmethod
    def apply(self, fields: typing.MutableMapping, response: httpx.Response) -> None:
        pass


class PropertyAnnotation(abc.ABC):
    _name: str
    _type: type

    def supply_formal(self, name: str, type_: type) -> None:
        self._name = name
        self._type = type_


class Body(ResponsePartHandler, PropertyAnnotation):
    _parse: Callable[[bytes], typing.Any]

    def supply_formal(self, name: str, type_: type) -> None:
        super().supply_formal(name, type_)
        self._parse = pydantic.TypeAdapter(type_).validate_json

    def apply(self, fields: typing.MutableMapping, response: httpx.Response) -> None:
        fields[self._name] = self._parse(response.content)


class Header(ResponsePartHandler, PropertyAnnotation):
    def __init__(self, header: str) -> None:
        self._header = header

    def apply(self, fields: typing.MutableMapping, response: httpx.Response) -> None:
        fields[self._name] = response.headers.get(self._header, None)


class ResponseEnvelope(abc.ABC, pydantic.BaseModel):
    """Marker interface for response envelopes."""


BodyT = typing.TypeVar('BodyT')


class DefaultEnvelope(ResponseEnvelope, typing.Generic[BodyT]):
    body: typing.Annotated[BodyT, Body()]
