# Serializing request body

## Input

OpenAPI 3.x essentially defines the request body object as a mapping of media type (or media type range) to schema and encoding object.

This means that the server accepts various media types there may be different data types, but also it may be the same data type.

On the client side we have the type as the input, the mapping transforms to mapping of schema to a set of (media type or type range and encoding object).
That set needs to be resolved to a single media type.

This parameter only declares what is accepted by the server, and in some cases it might be insufficient to determine the request body serialization method. For this reason the operation method should accept, and in some cases require, the requests content-type.
