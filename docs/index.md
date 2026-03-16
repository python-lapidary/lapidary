# Lapidary

Python helper for creating Web API clients.

## Features

- [x] Write Web API clients declaratively
- [x] Use [pydantic](https://docs.pydantic.dev/latest/) models for JSON data
- [x] Compatibility with [OpenAPI](https://www.openapis.org/)
    - [x] 3.0
    - [ ] 3.1 (Planned)

## Installation

```console
pip install lapidary
```

or with Poetry

```console
poetry add lapidary
```

## Usage

With Lapidary, you define an API client by creating a class that mirrors the API structure, akin to OpenAPI but through
decorated and annotated Python methods. Calling these method handles making HTTP requests and transforming the responses
back into Python objects.

```python
from collections.abc import Awaitable
from typing import Annotated, Self
from lapidary.runtime import *


# Define models
class Cat(ModelBase):
    id: int
    name: str


# Declare the client
class CatClient:
    @get('/cat/{id}')
    async def cat_get(
        self: Self,
        *,
        id: Annotated[int, Path],
    ) -> Annotated[
        Awaitable[Cat],
        Responses({'2XX': Response(Body({'application/json': Cat}))}),
    ]:
        pass
```

User code

```python
import lapidary.runtime.client
import httpx


async def main():
    async with httpx.AsyncClient() as http:
        client = lapidary.runtime.client.for_api(CatClient, http, 'http://localhost:8080/api')
        cat = await client.cat_get(id=7)
```

See [this test file](https://github.com/python-lapidary/lapidary/blob/develop/tests/test_client.py) for a working
example.

Also check [clients](https://github.com/orgs/lapidary-library/repositories) generated with Lapidary Render.

## Prior work

- [Uplink 📡](https://uplink.prkumar.dev/) - more mature and full-featured but not designed with OpenAPI compatibility in mind.
- [aiopenapi3](https://github.com/commonism/aiopenapi3) - An OpenAPI client. aiopenapi3 interprets OpenAPI document and creates all the classes and functions at runtime, so it lacks suport for IDEs or type checkers.
