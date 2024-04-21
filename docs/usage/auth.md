# Authentication

## Model

Lapidary allows API client authors to declare security requirements using maps that specify acceptable security schemes
per request. OAuth2 schemes require specifying scopes, while other schemes use an empty list.

For example, a call might require authentication with either two specific schemes together (auth1 and auth2) or another
pair (auth3 and auth4):

```python
security = [
    {
        'auth1': ['scope1'],
        'auth2': ['scope1', 'scope2'],
    },
    {
        'auth3': ['scope3'],
        'auth4': [],
    },
]
```

Lapidary also supports optional authentication, allowing for certain operations, such as a login endpoint, to forego the
global security requirements specified for the API:

```python
security = [
    {'auth': []},
    {},  # unauthenticated calls allowed
]
```

You can also use this method to disable global security requirement for a particular operation (e.g. login endpoint).

## Usage

Lapidary handles security schemes through httpx.Auth instances, wrapped in `NamedAuth` tuple.
You can define security requirements globally in the client `__init__()` or at the operation level with decorators, where
operation-level declarations override global settings.

Lapidary validates security requirements at runtime, ensuring that any method call is accompanied by the necessary
authentication, as specified by its security requirements. This process involves matching the provided authentication
against the declared requirements before proceeding with the request. To meet these requirements, the user must have
previously configured the necessary Auth instances using lapidary_authenticate.

```python
from lapidary.runtime import *
from lapidary.runtime.auth import HeaderApiKey
from typing import Self, Annotated


class MyClient(ClientBase):
    def __init__(self):
        super().__init__(
            base_url=...,
            security=[{'apiKeyAuth': []}],
        )

    @get('/api/operation', security=[{'admin_only': []}])
    async def my_op(self: Self) -> ...:
        pass

    @post('/api/login', security=())
    async def login(
        self: Self,
        user: Annotated[str, ...],
        password: Annotated[str, ...],
    ) -> ...:
        pass

# User code
async def main():
    client = MyClient()

    token = await client.login().token
    client.lapidary_authenticate(apiKeyAuth=HeaderApiKey(token))
    await client.my_op()

    # optionally
    client.lapidary_deauthenticate('apiKeyAuth')
```

`lapidary_authenticate` also accepts tuples of Auth instances with names, so this is possible:

```python
def admin_auth(api_key: str) -> NamedAuth:
    return 'admin_only', HeaderApiKey(api_key)


client.lapidary_authencticate(admin_auth('my token'))
```

## De-registering Auth instances

To remove an auth instance, thereby allowing for unauthenticated calls or the use of alternative security schemes,
lapidary_deauthenticate is used:

```python
client.lapidary_deauthenticate('apiKeyAuth')
```
