# Client class

The core of the Lapidary API client is a single class that contains all the methods for API operations. This class is
built around an `httpx.AsyncClient` instance to manage HTTP requests and responses.

Example usage:

```python
from lapidary.runtime import *


class CatClient(ClientBase):
    ...
```

# `__init__()` method

Implementing the `__init__()` method is optional but useful for specifying default values for settings like
the `base_url` of the API.

Example implementation:

```python
import httpx
import lapidary.runtime


class CatClient(lapidary.runtime.ClientBase):
    def __init__(
        self,
        client: httpx.AsyncClient | None = None,
        base_url = 'https://example.com/api',
        **kwargs,
    ):
        super().__init__(
            client=client,
            base_url=base_url,
            **kwargs
        )
    ...
```

## Recommended request header User-Agent

HTTP request headers can be added using the standard httpx API. It's recommended to add User-Agent header.

```python
from importlib.metadata import version

import httpx


async with httpx.AsyncClient(
    headers={
        'User-Agent': f'my-project/{version("my_package")} (+https://example.com/project; project@example.com)',
    }
) as httpx_client:
    client = MyApiClient(httpx_client)
    # make requests
```
