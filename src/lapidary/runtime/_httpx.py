import httpx
import typing_extensions as typing

UseClientDefault: typing.TypeAlias = httpx._client.UseClientDefault  # pylint: disable=protected-access
PrimitiveData: typing.TypeAlias = httpx._types.PrimitiveData  # pylint: disable=protected-access
