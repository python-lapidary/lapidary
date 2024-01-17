In Lapidary, every method in the client class represents a single API operation on a path.

Compared to OpenAPI Operation, it has the same features, except more than one method can invoke the same method and path, for example to bind input parameters with output type.

# HTTP method and path

Every method in the client class, decorated with one of the decorators named after standard HTTP methods (GET, PUT, POST, etc., except CONNECT) becomes an operation method.

Other methods are ignored by Lapidary.

The decorator accepts path as the only parameter.

Note: in the examples below all functions are actually methods, with the encapsulating class omitted.

```python
@get('/cats')  # method and path
async def list_cats(...):
    pass
```

Other methods can be used with decorator `@Operation(method, path)`

# Parameters

Each parameter can either represent a single part of a HTTP request: header, cookie, query parameter, path parameter or body; or can be an instance of `httpx.Auth`.

Every parameter must be annotated, including `self`.

`*args` and `**kwargs` are not supported.

## Query parameters

Query parameters are appended to the URL after '?' character, e.g. `https://example.com/path?param=value`.

Query parameters are declared using `Query()` annotation:

```python
@get('/cats')
async def list_cats(
        self: Self,
        color: Annotated[str, Query()],
):
    pass
```

Calling this method as

```python
client.list_cats(color='black')
```

will results in making a GET request to `https://example.com/cats?color=black`

## Path parameters

Path parameters are variables in the requests path: `http://example.com/cat/{cat_id}`.

```python
@get('/cat/{cat_id}')
async def get_cat(
        self: Self,
        cat_id: Annotated[str, Path()],
):
    pass
```

Calling this method as

```python
client.get_cat(cat_id=1)
```

will result in making a GET request to 'https://example.com/cat/1'.

## Header parameters

Header parameter will simply add a HTTP header to the request.

```python
@get('/cats')
async def list_cats(
        self: Self,
        accept: Annotated[str, Header('Accept')],
):
    pass
```

Calling this method as

```python
client.list_cats(accept='application/json')
```

will result in making a GET request with added header `Accept: application/json`.

Note: all of Cookie, Header, Param and Query annotations accept name, style and explode parameters, as defined by OpenAPI.

## Cookie parameters

Cookie parameter will add a `name=value` to the `Cookie` header of the request.

```python
@get('/cats')
async def list_cats(
        self: Self,
        cookie_key: Annotated[str, Cookie('key')],
):
    pass
```

Calling this method as

```python
client.list_cats(cookie_key='value')
```

will result in making a GET request with added header `Cookie: key=value`.

## Request body

A Parameter annotated with `RequestBody` will be serialized as the HTTP requests body. At most one parameter can be a request body.

```python
@POST('/cat')
async def add_cat(
        self: Self,
        cat: Annotated[Cat, RequestBody({
            'application/json': Cat,
        })],
):
    pass
```

The type (here `Cat`) must be either a supported scalar value (str, int, float, date, datetime, or UUID) or a Pydantic model.

Calling this method will result in making a HTTP request with header `Content-Type: application/json` and the `cat` object serialized with Pydantics `BaseModel.model_dump_json()` as the request body.

# Return type

The `Responses` annotation maps `status code` template and `Content-Type` response header to a type,
and optionally allows converting the response body to an instance of `httpx.Auth`
class.

```python
@get('/cat')
async def list_cats(
        self: Self,
        cat: Annotated[Cat, RequestBody({
            'application/json': Cat,
        })],
) -> Annotated[
    List[Cat],
    Responses({
        '2XX': {
            'application/json': List[Cat],
        },
    })
]:
    pass
```

After a HTTP response is received, Lapidary checks the status code templates (here `2XX`) and the `Content-Type` header to find the expected python type, and use it to parse the response body.

## Login operations

Operation methods can accept one or more auth parameters.

```python
@GET('/cat')
async def list_cats(
        self: Self,
        cat: Annotated[Cat, RequestBody({
            'application/json': Cat,
        })],
        auth: Auth,
) -> Annotated[
    List[Cat],
    Responses({
        '2XX': {
            'application/json': List[Cat],
        },
    })
]:
    pass
```

Operation methods can also return Auth objects.

```python
@POST('/login')
async def login(
        self: Self,
        body: Annotated[LoginRequest, RequestBody()],
) -> Annotated[
    Auth,
    Responses({
        '2XX': {
            'application/json': Annotated[
                LoginResponse,
                APIKeyAuth(
                    'header',
                    'Authorization',
                    'Token {body.api_key}'
                ),
            ],
        },
    })
]:
    pass
```

In this case, an additional `APIKeyAuth` annotation is used. it parses the response and returns `httpx.Auth` instance, which can be used as a parameter value for a call to `list_cats()`.

If any type in the Responses map is a subclass of `Exception`, it will be raised instead of being returned.
