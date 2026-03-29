from collections.abc import Callable

import pydantic
import typing_extensions as typing

TypeAdapter: typing.TypeAlias = Callable[[typing.Any], typing.Any]


def mk_type_adapter(typ: type, json: bool) -> TypeAdapter:
    adapter = pydantic.TypeAdapter(typ)
    return adapter.validate_json if json else adapter.validate_python
