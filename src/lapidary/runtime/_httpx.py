import httpx
import typing_extensions as typing

UseClientDefault: typing.TypeAlias = httpx._client.UseClientDefault  # pylint: disable=protected-access
PrimitiveData: typing.TypeAlias = httpx._types.PrimitiveData  # pylint: disable=protected-access
ParamValue: typing.TypeAlias = typing.Union[PrimitiveData, typing.Sequence[PrimitiveData]]
AuthType: typing.TypeAlias = typing.Union[httpx.Auth, UseClientDefault, None]
