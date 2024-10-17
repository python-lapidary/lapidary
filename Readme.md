# Lapidary

[![test](https://github.com/python-lapidary/lapidary/actions/workflows/test_publish.yaml/badge.svg)](https://github.com/python-lapidary/lapidary/actions/workflows/test_publsh.yaml)

Python DSL for Web API clients.

http://lapidary.dev/

## Why

DRY. Web API clients follow a relatively small set of patterns and writing them is rather repetitive task. Encoding these patterns in form of a DSL library frees its users from implementing the same patterns over and over again.

## How

Lapidary is an internal DSL made of decorators and annotations, that can be used to describe Web APIs similarly to OpenAPI
([lapidary-render](https://github.com/python-lapidary/lapidary-render/) can convert a large subset of OpenAPI 3.0 to Lapidary).

At runtime, the library interprets user-provided function declarations (without bodies), and makes them behave as declared. If a function accepts parameter of type `X` and returns `Y`, Lapidary will try to convert `X` to HTTP request and the response to `Y`.

### Example:

```python
class CatClient(ClientBase):
    """This class is a working API client"""

    def __init__(self):
        super().__init__(
            base_url='https://example.com/api',
        )

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
```
