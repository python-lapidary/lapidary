import functools as ft

from .compat import typing as ty
from .model.params import Param, ParamLocation, ParamStyle


def _mk_param(
        location: ParamLocation,
        name: ty.Optional[str] = None,
        style: ty.Optional[ParamStyle] = None,
        explode: ty.Optional[bool] = None,
) -> Param:
    return Param(
        alias=name,
        location=location,
        style=style,
        explode=explode,
    )


Cookie = ft.partial(_mk_param, ParamLocation.cookie)
Header = ft.partial(_mk_param, ParamLocation.header)
Path = ft.partial(_mk_param, ParamLocation.path)
Query = ft.partial(_mk_param, ParamLocation.query)
