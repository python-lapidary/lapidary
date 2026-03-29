from collections.abc import AsyncIterable, Awaitable, Callable
from typing import TypeVar

from typing_extensions import ParamSpec

P = ParamSpec('P')
R = TypeVar('R')
C = TypeVar('C')


def iter_pages(
    fn: Callable[P, Awaitable[R]],
    cursor_param_name: str,
    get_cursor: Callable[[R], C | None],
) -> Callable[P, AsyncIterable[R]]:
    """
    Take a function that returns a pageg response and return a function that returns an async iterator that iterates over the pages.

    The returned function can be called with the same parameters as :param:`fn` (except for the cursor parameter),
    and returns an async iterator that yields results from :param:`fn`, handling pagination automatically.

    The function :param:`fn` will be called initially without the cursor parameter and then called with the cursor parameter
    as long as :param:`get_cursor` can extract a cursor from the result.

    Example::

    async for page in iter_pages(client.ops.fn, 'cursor', get_cursor_from_response)(parameter=value):
        # Process page

    :param fn: An async function that retrieves a page of data.
    :param cursor_param_name: The name of the cursor parameter in :param:`fn`.
    :param get_cursor: A function that extracts a cursor value from the result of :param:`fn`. Return `None` to end the iteration.
    """

    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> AsyncIterable[R]:
        result = await fn(*args, **kwargs)  # type: ignore[call-arg]
        yield result
        cursor = get_cursor(result)

        while cursor:
            kwargs[cursor_param_name] = cursor
            result = await fn(*args, **kwargs)  # type: ignore[call-arg]
            yield result

            cursor = get_cursor(result)

    return wrapper
