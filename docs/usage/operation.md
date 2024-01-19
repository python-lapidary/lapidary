Methods decorated with one of `@get`, `@post`, `@put`, etc. become operation methods, calling them will make a HTTP exchange.
Lapidary supports the same HTTP methods as OpenAPI 3.x, i.e. methods listed in RFC 9110 except CONNECT.

Other methods are ignored.

!!! note methods

    Python methods and HTTP methods are completely different things.

    In this documentation, a `method` (in programming context) always means a python method (`def`), while HTTP methods (GET, POST, ...) are always referred to as `HTTP methods`.

```python
from lapidary.runtime import ClientBase, get


class CatClient(ClientBase):

    @get('/cats')
    async def list_cats(...):
        pass
```

!!! note

    In the examples below, methods are written as functions, omitting the encapsulating class.

```python
@get('/cats')  # method and path
async def list_cats(...):
    pass
```

## Parameters

Each parameter can represent a single part of a HTTP request: header, cookie cookie, query or path parameter, body, or auth flow (`httpx.Auth`).

Every parameter must be annotated, including `self`. `*args` and `**kwargs` are not supported.

### Query parameters

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

### Path parameters

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

## Headers

### Non-cookie headers

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

### Cookie headers

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

## Return type

The `Responses` annotation maps `status code` template and `Content-Type` response header to a type.

Note that the return type or types are mentioned in two places:

The first time in the top Annotated, it declares the return type of the method. It can be a Union type if the operation returns differently structured response bodies.

The second time is inside of responses. It tells Lapidary what type to use to process the response body when the response has a matching HTTP status code and content type.

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

The `dict` passed to `Responses` says that when response status code is one of 200s, and Content-Type is 'application/json', the response body is to be parsed as `list` of `Cat` objects.

### Response body post-processing

You can annotate the type inside `Responses` with additional pos-processors.

Lapidary accepts a list of `callable`s and calls them in a sequence, passing the result of the previous callable to the next one.

Operation methods can accept one or more auth parameters.

```python
    Responses({
    '2XX': {
        'application/json': Annotated[
            ResponseParseType,
            post_process1,
            post_process2,
        ],
    },
})
```

In this example, the request body is parsed as `ResponseParseType`,
that object is passed to `post_process1` function,
it's result is then passed to `post+process2`,
and that result is returned by the operation method.

For the best developer experience, make sure that whatever the last post-processor callable returns, it matches the type in the return type annotation.

An example application of post-processing is returning `Auth` flow objects from [login methods](auth.md#login-endpoints).

### Raising exceptions

If the matched response body type is an `Exception`, it will be raised instead of being returned.

```python
from dataclasses import dataclass


class ErrorModel(Exception):
    error_code: int
    error_message: str


@get('/cat')
async def list_cats(
        self: Self,
) -> Annotated[
    List[Cat],
    Responses({
        '2XX': {...},
        '4XX': {
            'application/json': ErrorModel,
        }
    }),
]:
    pass
```

!!! note

    When writing model type for the exception response, you can't use`pydantic.BaseModel`, since it's incompatible with `Exception` for multiple inheritance.

    Instead write a plain class or a `dataclass`.

!!! note

    Just like when writing normal python functions, there's no need to add exception types to the return type annotation.
