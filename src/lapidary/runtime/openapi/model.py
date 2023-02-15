# generated by datamodel-codegen:
#   filename:  schema.yaml

from __future__ import annotations

import re
from collections.abc import Mapping
from enum import Enum
from typing_extensions import Annotated
from typing import Any, Dict, List, Optional, Union, Tuple

from pydantic import AnyUrl, BaseModel, EmailStr, Extra, Field, validator, root_validator, parse_obj_as

from .base import ExtendableModel, DynamicExtendableModel, cross_validate_content
from .ext import PluginModel, LapidaryModelType

__all__ = [
    'APIKeySecurityScheme',
    'AuthorizationCodeOAuthFlow',
    'Callback',
    'ClientCredentialsFlow',
    'Components',
    'Contact',
    'Discriminator',
    'Encoding',
    'Example',
    'ExternalDocumentation',
    'HTTPSecurityScheme',
    'Header',
    'ImplicitOAuthFlow',
    'In',
    'In1',
    'In2',
    'In3',
    'In4',
    'Info',
    'License',
    'Link',
    'MediaType',
    'OAuth2SecurityScheme',
    'OAuthFlows',
    'OpenApiModel',
    'OpenIdConnectSecurityScheme',
    'Operation',
    'Parameter',
    'ParameterLocation',
    'ParameterLocationItem',
    'ParameterLocationItem1',
    'ParameterLocationItem2',
    'ParameterLocationItem3',
    'PasswordOAuthFlow',
    'PathItem',
    'Paths',
    'Reference',
    'RequestBody',
    'Required',
    'Response',
    'Responses',
    'Schema',
    'SecurityRequirement',
    'SecurityScheme',
    'Server',
    'ServerVariable',
    'Style',
    'Style1',
    'Style2',
    'Style4',
    'Tag',
    'Type',
    'Type1',
    'Type2',
    'Type3',
    'Type4',
    'XML'
]


class Reference(BaseModel):
    class Config:
        allow_population_by_field_name = True

    ref: Annotated[str, Field(alias='$ref')]


class Contact(ExtendableModel):
    name: Optional[str]
    url: Optional[str]
    email: Optional[EmailStr]


class License(ExtendableModel):
    name: str
    url: Optional[str]


class ServerVariable(ExtendableModel):
    enum: Optional[List[str]]
    default: str
    description: Optional[str]


class Type(Enum):
    array = 'array'
    boolean = 'boolean'
    integer = 'integer'
    number = 'number'
    object = 'object'
    string = 'string'


class Discriminator(BaseModel):
    propertyName: str
    mapping: Optional[Dict[str, str]]


class XML(ExtendableModel):
    name: Optional[str]
    namespace: Optional[AnyUrl]
    prefix: Optional[str]
    attribute: Optional[bool] = False
    wrapped: Optional[bool] = False


class Example(ExtendableModel):
    summary: Optional[str]
    description: Optional[str]
    value: Optional[Any]
    externalValue: Optional[str]


class Style(Enum):
    simple = 'simple'


class SecurityRequirement(BaseModel):
    __root__: Annotated[Dict[str, List[str]], Field(default_factory=dict)]


class ExternalDocumentation(ExtendableModel):
    description: Optional[str]
    url: str


class ExampleXORExamples(BaseModel):
    __root__: Annotated[
        Any,
        Field(
            description='Example and examples are mutually exclusive',
            not_={'required': ['example', 'examples']},
        ),
    ]


class In(Enum):
    path = 'path'


class Style1(Enum):
    matrix = 'matrix'
    label = 'label'
    simple = 'simple'


class Required(Enum):
    bool_True = True


class ParameterLocationItem(BaseModel):
    """
    Parameter in path
    """

    in_: Annotated[Optional[In], Field(alias='in')]
    style: Optional[Style1] = Style1.simple
    required: Required

    class Config:
        extra = Extra.forbid
        allow_population_by_field_name = True


class In1(Enum):
    query = 'query'


class Style2(Enum):
    form = 'form'
    spaceDelimited = 'spaceDelimited'
    pipeDelimited = 'pipeDelimited'
    deepObject = 'deepObject'


class ParameterLocationItem1(BaseModel):
    """
    Parameter in query
    """

    in_: Annotated[Optional[In1], Field(alias='in')]
    style: Optional[Style2] = Style2.form

    class Config:
        extra = Extra.forbid
        allow_population_by_field_name = True


class In2(Enum):
    header = 'header'


class ParameterLocationItem2(BaseModel):
    """
    Parameter in header
    """

    in_: Annotated[Optional[In2], Field(alias='in')]
    style: Optional[Style] = Style.simple

    class Config:
        extra = Extra.forbid
        allow_population_by_field_name = True


class In3(Enum):
    cookie = 'cookie'


class Style4(Enum):
    form = 'form'


class ParameterLocationItem3(BaseModel):
    """
    Parameter in cookie
    """

    in_: Annotated[Optional[In3], Field(alias='in')]
    style: Optional[Style4] = Style4.form

    class Config:
        extra = Extra.forbid
        allow_population_by_field_name = True


class ParameterLocation(BaseModel):
    __root__: Annotated[
        Union[
            ParameterLocationItem,
            ParameterLocationItem1,
            ParameterLocationItem2,
            ParameterLocationItem3,
        ],
        Field(description='Parameter location'),
    ]


class Type1(Enum):
    apiKey = 'apiKey'


class In4(Enum):
    header = 'header'
    query = 'query'
    cookie = 'cookie'


class APIKeySecurityScheme(ExtendableModel):
    class Config(ExtendableModel.Config):
        allow_population_by_field_name = True

    type: Type1
    name: str
    in_: Annotated[In4, Field(alias='in')]
    description: Optional[str]


class Type2(Enum):
    http = 'http'


class HTTPSecurityScheme(ExtendableModel):
    scheme: str
    bearerFormat: Optional[str]
    description: Optional[str]
    type: Type2

    @validator('bearerFormat', allow_reuse=True)
    def _validate_bearer_format(cls, value: str, values: Mapping[str, Any]) -> str:
        if values['scheme'].lower() != 'bearer':
            raise ValueError('bearerFormat is only allowed if "schema" is "bearer"')

        return value


class Type3(Enum):
    oauth2 = 'oauth2'


class Type4(Enum):
    openIdConnect = 'openIdConnect'


class OpenIdConnectSecurityScheme(BaseModel):
    class Config:
        extra = Extra.forbid

    type: Type4
    openIdConnectUrl: str
    description: Optional[str]


class ImplicitOAuthFlow(BaseModel):
    class Config:
        extra = Extra.forbid

    authorizationUrl: str
    refreshUrl: Optional[str]
    scopes: Dict[str, str]


class PasswordOAuthFlow(ExtendableModel):
    class Config:
        extra = Extra.forbid

    tokenUrl: str
    refreshUrl: Optional[str]
    scopes: Optional[Dict[str, str]]

    plugin: Annotated[Optional[str], Field(alias='x-plugin')]


class ClientCredentialsFlow(PasswordOAuthFlow):
    pass


class AuthorizationCodeOAuthFlow(BaseModel):
    class Config:
        extra = Extra.forbid

    authorizationUrl: str
    tokenUrl: str
    refreshUrl: Optional[str]
    scopes: Optional[Dict[str, str]]


class Info(ExtendableModel):
    title: str
    description: Optional[str]
    termsOfService: Optional[str]
    contact: Optional[Contact]
    license: Optional[License]
    version: str


class Server(ExtendableModel):
    url: str
    description: Optional[str]
    variables: Optional[Dict[str, ServerVariable]]


class Schema(ExtendableModel):
    class Config(ExtendableModel.Config):
        allow_population_by_field_name = True

    title: Optional[str]
    type: Optional[Type]

    # type == number or type == integer
    multipleOf: Annotated[Optional[float], Field(gt=0.0)]
    maximum: Optional[float]
    exclusiveMaximum: Optional[bool] = False
    minimum: Optional[float]
    exclusiveMinimum: Optional[bool] = False

    # type == string
    maxLength: Annotated[Optional[int], Field(ge=0)]
    minLength: Annotated[int, Field(ge=0)] = 0
    pattern: Optional[str]

    # type == array
    items: Optional[Union[Schema, Reference]]
    maxItems: Annotated[Optional[int], Field(ge=0)]
    minItems: Annotated[Optional[int], Field(ge=0)] = 0
    uniqueItems: Optional[bool] = False

    # type == object
    maxProperties: Annotated[Optional[int], Field(ge=0)]
    minProperties: Annotated[Optional[int], Field(ge=0)] = 0
    required: Annotated[Optional[List[str]], Field(min_items=1, unique_items=True)]
    properties: Optional[Dict[str, Union[Schema, Reference]]]
    additionalProperties: Optional[Union[Schema, Reference, bool]] = True

    # type == string or type = number or type == integer
    format: Optional[str]

    enum: Annotated[Optional[List], Field(min_items=1, unique_items=False)]

    not_: Annotated[Optional[Union[Schema, Reference]], Field(alias='not')]
    allOf: Optional[List[Union[Schema, Reference]]]
    oneOf: Optional[List[Union[Schema, Reference]]]
    anyOf: Optional[List[Union[Schema, Reference]]]

    description: Optional[str]
    default: Optional[Any]
    nullable: Optional[bool] = False
    discriminator: Optional[Discriminator]
    readOnly: Optional[bool] = False
    writeOnly: Optional[bool] = False
    example: Optional[Any]
    externalDocs: Optional[ExternalDocumentation]
    deprecated: Optional[bool] = False
    xml: Optional[XML]

    lapidary_names: Annotated[
        Optional[Dict[Union[str, None], Any]],
        Field(
            alias='x-lapidary-names',
            default_factory=dict,
            description="Mapping of keys used in the JSON document and variable names in the generated Python code. "
                        "Applicable to enum values or object properties."
        )
    ]
    lapidary_name: Annotated[Optional[str], Field(alias='x-lapidary-type-name')] = None
    lapidary_model_type: Annotated[Optional[LapidaryModelType], Field(alias='x-lapidary-modelType')] = None


class Tag(ExtendableModel):
    name: str
    description: Optional[str]
    externalDocs: Optional[ExternalDocumentation]


class OAuthFlows(BaseModel):
    class Config:
        extra = Extra.forbid

    implicit: Optional[ImplicitOAuthFlow]
    password: Optional[PasswordOAuthFlow]
    clientCredentials: Optional[ClientCredentialsFlow]
    authorizationCode: Optional[AuthorizationCodeOAuthFlow]


class Link(ExtendableModel):
    operationId: Optional[str]
    operationRef: Optional[str]
    parameters: Optional[Dict[str, Any]]
    requestBody: Optional[Any]
    description: Optional[str]
    server: Optional[Server]


class OAuth2SecurityScheme(BaseModel):
    class Config:
        extra = Extra.forbid

    type: Type3
    flows: OAuthFlows
    description: Optional[str]


class SecurityScheme(BaseModel):
    __root__: Union[
        APIKeySecurityScheme,
        HTTPSecurityScheme,
        OAuth2SecurityScheme,
        OpenIdConnectSecurityScheme,
    ]


class OpenApiModel(ExtendableModel):
    """
    Validation schema for OpenAPI Specification 3.0.X.
    """

    class Config(ExtendableModel.Config):
        allow_population_by_field_name = True

    openapi: Annotated[str, Field(regex='^3\\.0\\.\\d(-.+)?$')]
    info: Info
    externalDocs: Optional[ExternalDocumentation]
    servers: Optional[List[Server]]
    security: Optional[List[SecurityRequirement]]
    tags: Annotated[Optional[List[Tag]], Field(unique_items=True)]
    paths: Paths
    components: Optional[Components]

    lapidary_headers_global: Annotated[
        Optional[Union[
            Dict[str, Union[str, List[str]]],
            List[Tuple[str, str]]
        ]],
        Field(
            alias='x-lapidary-headers-global',
            description='Headers to add to every request.'
        )
    ] = None

    lapidary_responses_global: Responses = Field(
        alias='x-lapidary-responses-global',
        description='Base Responses. Values in Responses declared in Operations override values in this one.',
        default_factory=dict,
    )


class Components(ExtendableModel):
    schemas: Optional[Dict[str, Union[Schema, Reference]]]
    responses: Optional[Dict[str, Union[Reference, Response]]]
    parameters: Optional[Dict[str, Union[Reference, Parameter]]]
    examples: Optional[Dict[str, Union[Reference, Example]]]
    requestBodies: Optional[Dict[str, Union[Reference, RequestBody]]]
    headers: Optional[Dict[str, Union[Reference, Header]]]
    securitySchemes: Optional[Dict[str, Union[Reference, SecurityScheme]]]
    links: Optional[Dict[str, Union[Reference, Link]]]
    callbacks: Optional[Dict[str, Union[Reference, Callback]]]


class Response(ExtendableModel):
    description: str
    headers: Optional[Dict[str, Union[Header, Reference]]]
    content: Optional[Dict[str, MediaType]]
    links: Optional[Dict[str, Union[Link, Reference]]]


class MediaType(ExtendableModel):
    class Config(ExtendableModel.Config):
        allow_population_by_field_name = True

    schema_: Annotated[Optional[Union[Schema, Reference]], Field(alias='schema')]
    example: Optional[Any]
    examples: Optional[Dict[str, Union[Example, Reference]]]
    encoding: Optional[Dict[str, Encoding]]

    @validator('examples')
    def _validate_example_xor_examples(cls, value, values):
        if values.get('example'):
            raise ValueError('Only either example or examples is allowed')
        return parse_obj_as(Dict[str, Union[Example, Reference]], value)


class Header(ExtendableModel):
    description: Optional[str]
    required: Optional[bool] = False
    deprecated: Optional[bool] = False
    allowEmptyValue: Optional[bool] = False
    content: Annotated[
        Optional[Dict[str, MediaType]], Field(maxProperties=1, minProperties=1)
    ]
    style: Optional[Style] = Style.simple
    explode: Optional[bool]
    allowReserved: Optional[bool] = False
    schema_: Annotated[Optional[Union[Schema, Reference]], Field(alias='schema')]
    example: Optional[Any]
    examples: Optional[Dict[str, Union[Example, Reference]]]

    _validate_schema_xor_content = validator(
        'style', 'explode', 'allowReserved', 'schema_', 'example', 'examples',
        allow_reuse=True
    )(cross_validate_content)


class PathItem(ExtendableModel):
    summary: Optional[str]
    description: Optional[str]
    servers: Optional[List[Server]]
    parameters: Annotated[
        Optional[List[Union[Parameter, Reference]]], Field(unique_items=True)
    ]
    get: Optional[Operation]
    put: Optional[Operation]
    post: Optional[Operation]
    delete: Optional[Operation]
    options: Optional[Operation]
    head: Optional[Operation]
    patch: Optional[Operation]
    trace: Optional[Operation]


class Paths(DynamicExtendableModel[Union[PathItem, Reference]]):
    @classmethod
    def _validate_key(cls, key: str) -> bool:
        return key.startswith('/')


class Callback(DynamicExtendableModel[Union[PathItem, Reference]]):
    @classmethod
    def _validate_key(cls, key: str) -> bool:
        return True


class Operation(ExtendableModel):
    tags: Optional[List[str]]
    summary: Optional[str]
    description: Optional[str]
    externalDocs: Optional[ExternalDocumentation]
    operationId: Optional[str]
    parameters: Annotated[
        Optional[List[Union[Parameter, Reference]]], Field(unique_items=True)
    ]
    requestBody: Optional[Union[RequestBody, Reference]]
    responses: Responses
    callbacks: Optional[Dict[str, Union[Callback, Reference]]]
    deprecated: Optional[bool] = False
    security: Optional[List[SecurityRequirement]]
    servers: Optional[List[Server]]

    paging: Annotated[Optional[PluginModel], Field(alias='x-lapidary-pagingPlugin')]


class Responses(DynamicExtendableModel[Union[Response, Reference]]):
    @classmethod
    def _validate_key(cls, key: str) -> bool:
        return key == 'default' or bool(re.match(r'^[1-5](?:\d\d|XX)$', key))

    @root_validator
    def _validate_min_properties(cls, values):
        if not values:
            raise ValueError('minProperties')
        return values


class Parameter(ExtendableModel):
    class Config(ExtendableModel.Config):
        allow_population_by_field_name = True

    name: str
    in_: Annotated[str, Field(alias='in')]
    description: Optional[str]
    required: bool = False
    deprecated: bool = False
    allowEmptyValue: bool = False
    content: Annotated[
        Optional[Dict[str, MediaType]], Field(maxProperties=1, minProperties=1)
    ]
    style: Optional[str]
    explode: Optional[bool]
    allowReserved: Optional[bool] = False
    schema_: Annotated[Optional[Union[Schema, Reference]], Field(alias='schema')]
    example: Optional[Any]
    examples: Optional[Dict[str, Union[Example, Reference]]]

    lapidary_name: Annotated[Union[str, None], Field(alias='x-lapidary-name')] = None

    _validate_schema_xor_content = validator(
        'style', 'explode', 'allowReserved', 'schema_', 'example', 'examples',
        allow_reuse=True
    )(cross_validate_content)

    @property
    def effective_name(self) -> str:
        return self.lapidary_name or self.name


class RequestBody(ExtendableModel):
    description: Optional[str]
    content: Dict[str, MediaType]
    required: Optional[bool] = False


class Encoding(ExtendableModel):
    contentType: Optional[str]
    headers: Optional[Dict[str, Header]]
    style: Optional[Style2]
    explode: Optional[bool]
    allowReserved: Optional[bool] = False


Schema.update_forward_refs()
OpenApiModel.update_forward_refs()
Components.update_forward_refs()
Response.update_forward_refs()
MediaType.update_forward_refs()
PathItem.update_forward_refs()
Operation.update_forward_refs()
Paths.update_forward_refs()