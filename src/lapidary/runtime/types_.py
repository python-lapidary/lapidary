import httpx

from .compat import typing as ty

Serializer: ty.TypeAlias = ty.Callable[[ty.Any], ty.Union[str, bytes]]

# pylint: disable=protected-access
ParamValue: ty.TypeAlias = ty.Union[httpx._types.PrimitiveData, ty.Sequence[httpx._types.PrimitiveData]]
