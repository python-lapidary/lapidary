Methods decorated with one of @get, @post, @put, etc. are transformed into operation methods. Invoking these methods
initiates an HTTP request-response cycle. Lapidary is designed to be compatible with the HTTP methods defined in OpenAPI
3.x, which include all methods defined in RFC 9110, with the exception of CONNECT. Methods in your client that aren't
decorated with these operation decorators are simply ignored.

!!! note methods

    Python methods and HTTP methods represent two distinct concepts.

    Throughout this documentation, the term `method` in a programming context always refers to a Python method (defined with `def`), whereas `HTTP methods` (GET, POST, etc.) are specified as such.

```python
from lapidary.runtime import ClientBase, get


class CatClient(ClientBase):

    @get('/cats')
    async def list_cats(...):
        pass
```

!!! note

    In the examples below, methods are depicted as standalone functions, with the encapsulating class structure omitted.

```python
@get('/cats')  # method and path
async def list_cats(...):
    pass
```

## Parameters

Parameters within Lapidary are designed to represent different components of an HTTP request, including headers,
cookies, query parameters, path parameters, and the body of the request.

It's essential that every parameter, including self, is annotated to define its role and type explicitly. Note that *
args and **kwargs are not supported in this structure to maintain clarity and specificity in request definition.

### Query parameters

Query parameters are elements added to the URL following the '?' character, serving to modify or refine the request. An
example format is https://example.com/path?param=value.

To declare a query parameter in Lapidary, use the Query() annotation:

```python
@get('/cats')
async def list_cats(
        self: Self,
        color: Annotated[str, Query],
):
    pass
```

Calling a method like this:

```python
await client.list_cats(color='black')
```

results in a GET request being sent to the following URL: https://example.com/cats?color=black.

This illustrates how arguments passed to the method are directly mapped to query parameters in the URL, forming a
complete HTTP request based on the method's decoration and the parameters' annotations.

### Path parameters

Path parameters are variables embedded within the path of a request URL, such as http://example.com/cat/{cat_id}. These
parameters are essential for accessing specific resources or performing operations on them.

To define a path parameter in Lapidary, you use the path variable inside the decorator URL path and annotate the method
parameter with Path(). Here is an example of how to define and use a path parameter:

```python
@get('/cat/{cat_id}')
async def get_cat(
        self: Self,
        cat_id: Annotated[str, Path],
):
    pass
```

When you call this method like so:

```python
await client.get_cat(cat_id=1)
```

it constructs and sends a GET request to https://example.com/cat/1. This demonstrates the method's ability to
dynamically incorporate the provided argument (cat_id=1) into the request URL as a path parameter.

## Headers

### Non-cookie headers

Header parameters are utilized to add HTTP headers to a request. These can be defined using the `Header` annotation in a
method declaration, specifying the header name and the expected value type.

Example:

```python
@get('/cats')
async def list_cats(
        self: Self,
        version: Annotated[str, Header],
):
    pass
```

Invoking this method with:

```python
await client.list_cats(version='2')
```

results in the execution of a GET request that includes the header `version: 2`.

Note: The Cookie, Header, Param, and Query annotations all accept parameters such as name, style, and explode as defined
by OpenAPI.

### Cookie headers

To add a cookie to the request, you use the Cookie parameter. This adds a name=value pair to the Cookie header of the
HTTP request.

Example:

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
await client.list_cats(cookie_key='value')
```

will send a GET request that includes the header Cookie: key=value.

## Request body

To mark a parameter for serialization into the HTTP body, annotate it with RequestBody. Each method can include only one
such parameter.

Example:

```python
@POST('/cat')
async def add_cat(
        self: Self,
        cat: Annotated[Cat, Body({
            'application/json': Cat,
        })],
):
    pass
```

The parameter type, such as Cat in this example, should be a basic scalar (e.g., str, int, float, date, datetime, UUID)
or a Pydantic model, to facilitate proper serialization.

Invoking this method constructs a POST request with Content-Type: application/json header. The cat object is serialized
to JSON using Pydantic's BaseModel.model_dump_json() and included in the body of the request.

## Return type

The Responses annotation plays a crucial role in mapping HTTP status codes and Content-Type headers to specific return
types. This mechanism allows developers to define how responses are parsed and returned.

The return type is specified in two places:

1. At the method signature level - The declared return type here should reflect the expected successful response
   structure. It can be a single type or a Union of types, accommodating various potential non-error response bodies.

2. Within the `Responses` annotation - This details the specific type or types to be used for parsing the response body,
   depending on the response's HTTP status code and content type matching those specified.

!!! Note

    The type hint in the method's annotation must match the response types specified within the Responses() annotation, excluding exception types. For details on how to handle exception types, see the next section.

Example:

```python
@get('/cat')
async def list_cats(self: Self) -> Annotated[
    tuple[List[Cat], None],
    Responses({
        '2XX': Response(Body({
            'application/json': List[Cat],
        })),
    })
]:
    pass
```

In this setup, the Responses dictionary specifies that for responses with a 2XX status code and a Content-Type of
application/json, the response body will be parsed as a list of Cat objects. This explicit declaration ensures that the
method's return type is tightly coupled with the anticipated successful response structure, providing clarity and type
safety for API interactions.


### Mapping headers and response status code

Lapidary operation methods always return a tuple. The first element is the response body, the second is the response metadata (headers and/or status code), each of them being optional.

Example:

```python

class CatListMeta(ModelBase):
   total_count: Annotated[int, Header('Total-Count')]
   status_code: Annotated[int, StatusCode]


class CatClient(ClientBase):
   @get('/cat')
   async def list_cats(self: Self) -> Annotated[
       tuple[list[Cat], CatListMeta],
       Responses({
           '2XX': Response(
                Body({
                    'application/json': list[Cat],
                }),
                CatListMeta
           ),
       })
   ]:
       pass

client = CatClient()
cats_body, cats_meta = await client.list_cats()
assert cats_body.body == [Cat(...)]
assert cats_meta.count == 1
assert cats_meta.status_code == 200
```


### Handling error responses

Lapidary maps HTTP error responses to exceptions.

```python
class ErrorModel(ModelBase):
    error_code: int
    error_message: str


@get('/cat')
async def list_cats(
        self: Self,
) -> Annotated[
    tuple[List[Cat], None],
    Responses({
        '2XX': Response(...),
        '4XX': Response(Body({
            'application/json': ErrorModel,
        }))
    }),
]:
    pass
```

Responses with status code 400 and up will cause `HttpErrorResponse` to be risen as long as they're declared in the response map.

```python
try:
    await client.list_cats()
except HttpErrorResponse as e:
    assert e.status_code == 400
    assert e.headers is None
    assert isinstance(e.body, ErrorModel)
```

Any responses not declared in the response map, regardless of their status code, raise `UnexpectedResponse`.

```python
try:
    await client.list_cats()
except UnexpectedResponse as e:
    assert isinstance(e.response, httpx.response)
```

!!! note

    Exception types mapped to responses in the Responses annotation should not be included in the method's return type hint. They are exclusively declared within the Responses framework for appropriate processing.
