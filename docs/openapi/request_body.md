# Request body

## OpenAPI

OpenAPI 3.x defines the request object as a mapping of media type (or media type range, e.g. 'application/*') to encoding, schema and headers.

This means that the server accepts one or more data types under various media types.

On the client side we have the type as the input, which means we need to reverse the mapping, and in result we may end up with multiple media types or a media type range
but we need to send a single specific `Content-Type` header.

## Python

For such cases a `Header('Content-Type')` parameter can be used, and in such cases it should be required.
