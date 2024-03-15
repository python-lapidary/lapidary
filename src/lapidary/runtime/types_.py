import typing_extensions as typing

from . import _httpx

Serializer: typing.TypeAlias = typing.Callable[[typing.Any], typing.Union[str, bytes]]
ParamValue: typing.TypeAlias = typing.Union[_httpx.PrimitiveData, typing.Sequence[_httpx.PrimitiveData]]
