"""
Schema mapping
as class:

    title -  docstr
    maxItems: config - validation
    minItems: config - validation
    uniqueItems: config - validation
    maxProperties: config - validation
    minProperties: config - validation
    required: child attributes
    enum: enum class
    type: discriminator
    not_: config - validation
    allOf: superclasses
    oneOf: typing.Union
    anyOf: superclasses, all fields non-required, must validate against at least one superclass
    items: ignore this schema and generate class for the one declared here
    properties: attributes
    additionalProperties: unsupported
    description: docstr
    format: unused
    default: unsupported
    nullable: unused
    discriminator: unsupported
    readOnly: unused
    writeOnly: unused
    example: unused
    externalDocs: docstr
    deprecated: unused
    xml: unsupported


as attribute
    multipleOf: Field property
    maximum: Field property
    exclusiveMaximum: Field property
    minimum: Field property
    exclusiveMinimum: Field property
    maxLength: Field property
    minLength: Field property
    pattern: Field property
    maxItems: unused
    minItems: unused
    uniqueItems: unused
    maxProperties: unused
    minProperties: unused
    required: unused directly (passed as boolean)
    enum: unused
    type: type discriminator
    additionalProperties: unsupported
    format: type hint
    default: unsupported
    nullable: make Union[None, this]
    readOnly: Field property
    writeOnly: Field property
    deprecated: unsupported
    xml: unsupported


"""

from .attribute import get_attributes, AttributeModel
from .attribute_annotation import get_attr_annotation, AttributeAnnotationModel
from .client_class import ClientInit, get_client_init, get_client_class, ClientClass, get_operations
from .client_module import get_client_class_module, ClientModule
from .refs import ResolverFunc, get_resolver
from .request_body import get_request_body_module
from .response_body import get_response_body_module
from .schema_module import SchemaModule, get_modules_for_components_schemas, get_param_model_classes_module
