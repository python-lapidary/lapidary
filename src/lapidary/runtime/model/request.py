import dataclasses as dc

from ..compat import typing as ty
from lapidary.runtime.types_ import Serializer


@dc.dataclass(frozen=True)
class RequestBody:
    content: ty.Mapping[str, ty.Tuple[ty.Type, Serializer]]


@dc.dataclass(frozen=True)
class RequestBodyModel:
    param_name: str
    serializers: ty.Mapping[str, ty.Tuple[ty.Type, Serializer]]
