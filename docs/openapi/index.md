# Representing OpenAPI

The goal of python representation is to allow python code to fully replace OpanAPI document, allow Lapidary library to prepare a HTTP request and parse the response, in a way compatible with the
server described by that representation.

The python representation is fully self-sufficient, and doesn't require an OpenAPI document at runtime.

## Client

A client to a remote service may be represented as a collection of functions, each representing an operation, and a collection of data classes, each representing a schema.
The functions could be module-level or grouped in one or more classes, optionally forming an object hierarchy.

Lapidary currently implements a single class approach.

## Paths and Operations

OpenAPI `paths` object can be explained as a mapping of HTTP method and path to an Operation declaration.

OpenAPI Operation specifies the request body, parameters and responses, so it's the closest thing to a python function.

### Parameters

#### Naming

Each of cookie, header, path and query parameters have their own namespace, so they can't be directly mapped to names of parameters of a python function.

The possible workarounds are:

- grouping parameters in mappings, named tuples or objects,
- name mangling,
- annotations.

Lapidary uses annotations, which declares parameter location and may be used to provide the name.

```python
from typing import Annotated, Self
from lapidary.runtime import Cookie, ClientBase, Header

class Client(ClientBase):
    async def operation(
        self: Self,
        *,
        param1_c: Annotated[str, Cookie('param1')],
        param1_h: Annotated[str, Header('param1')],
    ):
        pass
```

#### Serialization

Serialization in OpenAPI is a rather complex subject, and not always defined well.

An example of undefined behaviour is serialization of nested object with simple or form style, which is neither defined nor forbidden.

Possible solution are:

- explicitly forbidding certain cases
- extending the specification, and optionally accepting extra parameters (i.e. field delimiter in nested objects)
- accepting custom de/serialization function

### Request Body

See [Request body](request_body.md)

### Responses

TODO

## Auth

See [Auth](../usage//auth.md).

## Servers

TODO
