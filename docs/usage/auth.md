# Authentication

## Behaviour

Lapidary uses a simple pattern for creating client instances with the required auth handlers.
Users can simply create their client instances with a `httpx.Auth` instance,
or make use of a simple shallow copy tool to clone an existing instance with an authenticator configured.

Lapidary doesn't validate whether a client has an authenticator required for a given operation,
since it can't know whether a server implies one scope from another.

## Usage

```python
import httpx
from lapidary.runtime import *
from lapidary.runtime.auth import HeaderApiKey
from typing import Self, Annotated


class MyClient(ClientBase):
    def __init__(self, client: httpx.AsyncClient):
        super().__init__(
            client=client,
            base_url='https://example.com/'
        )

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
    async with httpx.AsyncClient() as http_client:
        client = MyClient(http_client)

        token = (await client.login('username', 'secret')).token
        client_w_auth = with_auth(client, HeaderApiKey(token))

        await client_w_auth.my_op()
```
