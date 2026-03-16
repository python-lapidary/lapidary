import httpx
import typing_extensions as typing

UseClientDefault: typing.TypeAlias = httpx._client.UseClientDefault  # pylint: disable=protected-access
