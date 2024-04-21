# Client class

The core of the Lapidary API client is a single class that contains all the methods for API operations. This class is
built around an `httpx.AsyncClient` instance to manage HTTP requests and responses.

Example usage:

```python
from lapidary.runtime import *


class CatClient(ClientBase):
    ...
```

# `__init__()` method

Implementing the `__init__()` method is optional but useful for specifying default values for settings like
the `base_url` of the API.

Example implementation:

```python
import lapidary.runtime


class CatClient(lapidary.runtime.ClientBase):
    def __init__(
            self,
            base_url='https://example.com/api',
            **kwargs
    ):
        super().__init__(
            base_url=base_url,
            **kwargs
        )
    ...
```
