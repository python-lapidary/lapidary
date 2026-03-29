import abc
import dataclasses as dc
from collections.abc import Mapping

import pydantic
import typing_extensions as typing

from .model.param_serialization import FormExplode, MultimapSerializationStyle, SimpleMultimap, SimpleString, StringSerializationStyle
from .types_ import MimeType, StatusCodeRange


class WebArg(abc.ABC):
    """Base class for web-processed parameters."""


@dc.dataclass
class Body(WebArg):
    """
    Link content type headers with a python type.
    When used with a method parameter, it tells lapidary what content-type header to send for a given body type.
    When used in return annotation, it tells lapidary the type to process the response body as.

    Example use with parameter:

    .. code-block:: python

    body: Body({'application/json': BodyModel})
    """

    content: Mapping[MimeType, type]


class Metadata(WebArg):
    """
    Annotation for models that hold other WebArg fields.
    Can be used to group request parameters as an alternative to passing parameters directly.

    Example:

    .. code-block:: python

    class RequestMetadata(pydantic.BaseModel):
        my_header: typing.Annotated[
            str,
            Header('my-header'),
        ]

    class Client(ApiClient):
        @get(...)
        async def my_method(
            headers: Annotated[RequestMetadata, Metadata]
        ):
    """


class Param(WebArg, abc.ABC):
    """Base class for web parameters (headers, query and path parameters, including cookies)"""

    style: typing.Any
    alias: str | None

    def __init__(self, alias: str | None, /) -> None:
        self.alias = alias


class Header(Param):
    """Mark parameter as HTTP Header"""

    def __init__(
        self,
        alias: str | None = None,
        /,
        *,
        style: type[MultimapSerializationStyle] = SimpleMultimap,
    ) -> None:
        """
        :param alias: Header name, if different than the name of the annotated parameter
        :param style: Serialization style
        """
        super().__init__(alias)
        self.style = style


class Cookie(Param):
    def __init__(
        self,
        alias: str | None = None,
        /,
        *,
        style: type[MultimapSerializationStyle] = FormExplode,
    ) -> None:
        """
        :param alias: Cookie name, if different than the name of the annotated parameter
        :param style: Serialization style
        """
        super().__init__(alias)
        self.style = style


class Path(Param):
    def __init__(
        self,
        alias: str | None = None,
        /,
        *,
        style: type[StringSerializationStyle] = SimpleString,
    ) -> None:
        """
        :param alias: Path parameter name, if different than the name of the annotated parameter
        :param style: Serialization style
        """
        super().__init__(alias)
        self.style = style


class Query(Param):
    def __init__(
        self,
        alias: str | None = None,
        /,
        *,
        style: type[MultimapSerializationStyle] = FormExplode,
    ) -> None:
        """
        :param alias: Query parameter name, if different than the name of the annotated parameter
        :param style: Serialization style
        """
        super().__init__(alias)
        self.style = style


@dc.dataclass
class Link(WebArg):
    alias: str


class StatusCode(WebArg):
    pass


@dc.dataclass
class Response:
    """
    Declare the expected body and headers for a single HTTP response status code.

    Used as a value inside the :class:`Responses` mapping.

    Example:

    .. code-block:: python

    Response(Body({'application/json': Cat}))

    Response(Body({'application/json': Cat}), CatListMeta)
    """

    body: Body
    headers: type[pydantic.BaseModel] | None = None
    """Pydantic model to deserialize response headers into. Fields must be annotated with :class:`Header` or :class:`StatusCode`."""


@dc.dataclass
class Responses(WebArg):
    """
    Mapping between response code, headers, media type and body type.
    The simplified structure is:

        response code => (
            body: content type => body model type
            headers model
        )

    The structure follows OpenAPI 3.
    """

    responses: Mapping[StatusCodeRange, Response]
    """
    Map of status code match to Response.
    Key may be:

    - any HTTP status code
    - HTTP status code range, i.e. 1XX, 2XX, etc
    - "default"

    The most specific value takes precedence.
    """
