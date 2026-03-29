# Authentication

## Behaviour

Lapidary uses a simple pattern for authentication. Pass an `httpx.Auth` instance when creating a client via `for_api()`,
or create a new client object with a different authenticator using `APIClient.with_auth()`.

Lapidary doesn't validate whether a client has an authenticator required for a given operation,
since it can't know whether a server implies one scope from another.

## Usage

```python
import httpx
import lapidary.client
from lapidary import *
from lapidary import HeaderApiKey
from typing import Self, Annotated


class LoginRequest(ModelBase):
    username: str
    password: str


class LoginResponse(ModelBase):
    token: str


class MyClient:
    @get('/api/operation')
    async def my_op(self: Self) -> ...:
        pass

    @post('/api/login')
    async def login(
        self: Self,
        *,
        body: Annotated[LoginRequest, Body({'application/json': LoginRequest})],
    ) -> Annotated[
        tuple[LoginResponse, None],
        Responses({'2XX': Response(Body({'application/json': LoginResponse}))}),
    ]:
        pass


# User code
async def main():
    async with httpx.AsyncClient() as http:
        client = lapidary.client.for_api(MyClient, http, 'https://example.com/')

        response, _ = await client.ops.login(body=LoginRequest(username='user', password='secret'))
        client_w_auth = client.with_auth(HeaderApiKey(response.token))

        await client_w_auth.ops.my_op()
```
