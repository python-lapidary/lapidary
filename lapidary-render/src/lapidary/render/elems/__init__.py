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
