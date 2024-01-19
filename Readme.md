[![test](https://github.com/python-lapidary/lapidary/actions/workflows/test.yaml/badge.svg)](https://github.com/python-lapidary/lapidary/actions/workflows/test.yaml)

# Lapidary

Python DSL for Web API clients.

Also check [lapidary-render](https://github.com/python-lapidary/lapidary-render/),
a command line program that generates Lapidary client code from OpenAPI documents.

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

```python
import dataclasses as dc
from typing import Annotated, Self

import pydantic

from lapidary.runtime import ClientBase, ParamStyle, Path, Responses, get


# Define models
# Pydantic models are recommended, but classes cannot inherit from both BaseModel and Exception.

@dc.dataclass
class ServerError(Exception):
    msg: str


class Cat(pydantic.BaseModel):
    id: int
    name: str

# Declare the client

class CatClient(ClientBase):
    def __init__(
            self,
            base_url = 'http://localhost:8080/api',
    ):
        super().__init__(base_url=base_url)

    # Parameters are interpreted according to their annotation.
    # Response is parsed according to the return type annotation.

    @get('/cat/{id}')
    async def cat_get(
            self: Self,
            *,
            id: Annotated[int, Path(style=ParamStyle.simple)],
    ) -> Annotated[Cat, Responses({
        '2XX': {
            'application/json': Cat
        },
        '4XX': {
            'application/json': ServerError
        },
    })]:
        pass

client = CatClient()
cat = await client.cat_get(id=7)
```

See [this test file](https://github.com/python-lapidary/lapidary/blob/develop/tests/test_client.py) for a working example.

[Full documentation](https://lapidary.dev)

Also check the [library of clients](https://github.com/orgs/lapidary-library/repositories).
