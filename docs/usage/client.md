# Client class

The core of the Lapidary API client is a single class that declares all the methods. Pass it to `for_api()`
along with an `httpx.AsyncClient` instance and a base URL to get an `APIClient`. Operations are then accessed via `.ops`.

```python
async with httpx.AsyncClient() as http:
    client = lapidary.client.for_api(CatClient, http, 'https://example.com')
    result, _ = await client.ops.some_operation()
```

`for_api()` also accepts `auth` (see [Authentication](auth.md)) and `middlewares` (see [Middleware](middleware.md)).

## Additional HTTP headers

HTTP request headers can be added using the standard httpx API. It's recommended to add User-Agent header.

```python
from importlib.metadata import version

import httpx


async with httpx.AsyncClient(
    headers={
        'User-Agent': f'my-project/{version("my_project")} (+https://example.com/project; project@example.com)',
    }
) as http:
    client = ...
```
