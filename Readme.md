# Lapidary

[![test](https://github.com/python-lapidary/lapidary/actions/workflows/test_publish.yaml/badge.svg)](https://github.com/python-lapidary/lapidary/actions/workflows/test_publsh.yaml)

Python DSL for Web API clients.

http://lapidary.dev/

Also check [lapidary-render](https://github.com/python-lapidary/lapidary-render/),
a command line program that generates Lapidary clients from OpenAPI.

## Usage:

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
