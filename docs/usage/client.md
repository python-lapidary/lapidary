# Client class

Lapidary client is represented by a single class that holds all operation methods and encapsulates a `httpx.AsyncClient` instance.

```python
import lapidary.runtime


class CatClient(lapidary.runtime.ClientBase):
    ...
```

# `__init__()` method

Implementing `__init__()` is optional, and provides means to pass arguments, like `base_url`, to `httpx.AsyncClient.__init__`.

```python
import lapidary.runtime


class CatClient(lapidary.runtime.ClientBase):
    def __init__(
            self,
            base_url='https://example.com/api'
    ):
        super().__init__(
            base_url=base_url,
        )

    ...
```
