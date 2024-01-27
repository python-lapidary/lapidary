import httpx
import typing_extensions as typing

Serializer: typing.TypeAlias = typing.Callable[[typing.Any], typing.Union[str, bytes]]

# pylint: disable=protected-access
ParamValue: typing.TypeAlias = typing.Union[httpx._types.PrimitiveData, typing.Sequence[httpx._types.PrimitiveData]]
