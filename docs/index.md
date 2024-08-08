# Lapidary

Python DSL for Web API clients.

## Features

- [x] Write Web API clients declaratively
- [x] Use pydantic models for JSON data
- [ ] Compatibility with OpenAPI 3.0 and 3.1

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

class CatClient(ClientBase):
    def __init__(
        self,
        base_url='http://localhost:8080/api',
    ):
        super().__init__(base_url=base_url)

    @get('/cat/{id}')
    async def cat_get(
        self: Self,
        *,
        id: Annotated[int, Path],
    ) -> Annotated[Awaitable[Cat], Responses({
        '2XX': Response(Body({
            'application/json': Cat
        })),
    })]:
        pass

# User code

async def main():
    client = CatClient()
    cat = await client.cat_get(id=7)
```

See [this test file](https://github.com/python-lapidary/lapidary/blob/develop/tests/test_client.py) for a working
example.

[Full documentation](https://lapidary.dev)

Also check the [library of clients](https://github.com/orgs/lapidary-library/repositories).
