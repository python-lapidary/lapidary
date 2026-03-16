# Authentication

## Behaviour

Lapidary uses a simple pattern for authentication. Pass an `httpx.Auth` instance when creating a client via `for_api()`,
or create a new client object with a different authenticator using `APIClient.with_auth()`.

Lapidary doesn't validate whether a client has an authenticator required for a given operation,
since it can't know whether a server implies one scope from another.

## Usage

```python
import httpx
import lapidary.runtime.client
from lapidary.runtime import *
from lapidary.runtime.auth import HeaderApiKey
from typing import Self, Annotated


class MyClient:
    @get('/api/operation')
    async def my_op(self: Self) -> ...:
        pass

    @post('/api/login')
    async def login(
        self: Self,
        user: Annotated[str, ...],
        password: Annotated[str, ...],
    ) -> ...:
        pass


# User code
async def main():
    async with httpx.AsyncClient() as http:
        client = lapidary.runtime.client.for_api(MyClient, http, 'https://example.com/')

        token = (await client.ops.login('username', 'secret')).token
        client_w_auth = client.with_auth(client, HeaderApiKey(token))

        await client_w_auth.ops.my_op()
```
