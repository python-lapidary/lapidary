import httpx
import httpx_auth
import typing_extensions as typing

MultiAuth: typing.TypeAlias = httpx_auth._authentication._MultiAuth  # pylint: disable=protected-access
NamedAuth: typing.TypeAlias = tuple[str, httpx.Auth]
SecurityRequirements: typing.TypeAlias = typing.Mapping[str, typing.Iterable[str]]
