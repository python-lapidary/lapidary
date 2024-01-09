import dataclasses as dc

from ..compat import typing as ty


@dc.dataclass(frozen=True)
class RequestBody:
    content: ty.Mapping[str, ty.Type]


@dc.dataclass(frozen=True)
class RequestBodyModel:
    param_name: str
    serializers: ty.Mapping[str, ty.Type]
