import abc

import httpx
import pydantic
import typing_extensions as typing


class ResponseHandler(abc.ABC):
    @abc.abstractmethod
    def apply_response(self, response: httpx.Response, fields: typing.MutableMapping[str, typing.Any]) -> None:
        pass


class ResponseEnvelope(abc.ABC, pydantic.BaseModel):
    """Marker interface for response envelopes."""
