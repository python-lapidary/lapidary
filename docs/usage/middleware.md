Lapidary has a simple middleware mechanism borrowed from aiohttp.
It can be used to access lower-level HTTP request & response objects, for example in order to work around certain kinds of quirks in HTTP API implementations.

Fox example, a server may declare response media type as `application/json`, it may require `Accept` header, but will respond with some other header value.
Currently, lapidary requires the response `Content-Type` to be one of the values declared in the operation method response map.

A workaround for this issue might be the following middleware class:

```python
async def fix_content_type(request: httpx.Request, next_: Next) -> httpx.Response:
    # send the request verbatim
    response = await next_(request)

    # fix the response `Content-Type` header
    response.headers['Content-Type'] = 'application/json'

    return response
```
