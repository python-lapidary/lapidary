from .compat import typing as ty

Serializer: ty.TypeAlias = ty.Callable[[ty.Any], ty.Union[str, bytes]]
RequestContent: ty.TypeAlias = ty.Union[str, bytes, ty.Iterable[bytes], ty.AsyncIterable[bytes]]
