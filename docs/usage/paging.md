# Paging

`iter_pages` wraps an operation method and returns a function that, when called, yields successive pages as an async iterator.

```python
from lapidary import iter_pages


async def get_cursor(result: tuple[list[Cat], None]) -> str | None:
    body, _ = result
    return body.next_cursor if body.next_cursor else None


paginated = iter_pages(client.ops.list_cats, 'cursor', get_cursor)

async for page in paginated(color='black'):
    body, _ = page
    process(body)
```

The wrapped function is called first without the cursor parameter. After each call, `get_cursor` is invoked on the result. Iteration stops when `get_cursor` returns `None`.


## Shortcut

Since an API typically uses the same paging pattern for all its operations, it's practical to define a project-level helper:

```python
from lapidary import iter_pages as _iter_pages


def iter_pages[P, R](fn: Callable[P, Awaitable[R]]) -> Callable[P, AsyncIterable[R]]:
    return _iter_pages(fn, 'cursor', lambda result: result[0].next_cursor or None)
```
