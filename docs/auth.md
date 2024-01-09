# Authentication

OpenAPI allows declaring security schemes and security requirements of operations.

Lapidary allows to declare python methods that create or consume `https.Auth` objects.

## Generating auth tokens


A `/login/` or `/authenticate/` endpoint that returns the token is quite common with simpler authentication schemes like http or apiKey, yet their support is poor in OpenAPI. There's no way to connect
such endpoint to a security scheme as in the case of OIDC.

A function that handles such an endpoint can declare that it returns an Auth object, but it's not obvious to the user of python API which security scheme the method returns.

```python
import pydantic
import typing_extensions as ty
from lapidary.runtime import POST, ClientBase, RequestBody, APIKeyAuth, Responses
from httpx import Auth


class LoginRequest(pydantic.BaseModel):
    ...


class LoginResponse(pydantic.BaseModel):
    token: str


class Client(ClientBase):
    @POST('/login')
    def login(
            self: ty.Self,
            *,
            body: ty.Annotated[LoginRequest, RequestBody({'application/json': LoginRequest})],
    ) -> ty.Annotated[
        Auth,
        Responses({
            '200': {
                'application/json': ty.Annotated[
                    LoginResponse,
                    APIKeyAuth(
                        in_='header',
                        name='Authorization',
                        format='Token {body.token}'
                    ),
                ]
            }
        }),
    ]:
        """Authenticates with the "primary" security scheme"""
```

The top return Annotated declares the returned type, the inner one declares the processing steps for the actual response.
First the response is parsed as LoginResponse, then that object is passed to ApiKeyAuth which is a callable object.

The result of the call, in this case an Auth object, is returned by the `login` function.

The innermost Annotated is not necessary from the python syntax standpoint. It's done this way since it kind of matches the semantics of Annotated, but it could be replaced with a simple tuple or other type in the future.

## Using auth tokens

OpenApi allows operations to declare a collection of alternative groups of security requirements.

The second most trivial example (the first being no security) is a single required security scheme.
```yaml
security:
- primary: []
```
The name of the security scheme corresponds to a key in `components.securitySchemes` object.

This can be represented as a simple parameter, named for example `primary_auth` and of type `httpx.Auth`.
The parameter could be annotated as `Optional` if the security requirement is optional for the operation.

In case of multiple alternative groups of security requirements, it gets harder to properly describe which schemes are required and in what combination.

Lapidary takes all passed `httpx.Auth` parameters and passes them to `httpx.AsyncClient.send(..., auth=auth_params)`, leaving the responsibility to select the right ones to the user.

If multiple `Auth` parameters are passed, they're wrapped in `lapidary.runtime.aauth.MultiAuth`, which is just reexported `_MultiAuth` from `https_auth` package.

#### Example

Auth object returned by the login operation declared in the above example can be used by another operation.

```python
from typing import Annotated, Self
from httpx import Auth
from lapidary.runtime import ClientBase, GET, POST


class Client(ClientBase):
    @POST('/login')
    def login(
            self: Self,
            body: ...,
    ) -> Annotated[
        Auth,
        ...
    ]:
        """Authenticates with the "primary" security scheme"""

    @GET('/private')
    def private(
            self: Self,
            *,
            primary_auth: Auth,
    ):
        pass
```

In this example the method `client.private` can be called with the auth object returned by `client.login`.
