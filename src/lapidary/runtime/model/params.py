import enum
from dataclasses import dataclass
from enum import unique, Enum
from typing import Type, cast, Union, Any

from .refs import ResolverFunc
from .type_hint import TypeHint
from .types import get_type_hint
from .. import openapi
from ..module_path import ModulePath
from ..names import get_param_python_name, PARAM_MODEL


class ParamDirection(enum.Flag):
    """Use read for readOnly, write for writeOnly; read+write if unset"""

    read = enum.auto()
    write = enum.auto()


class ParamLocation(enum.Enum):
    cookie = 'cookie'
    header = 'header'
    path = 'path'
    query = 'query'

    def code(self) -> str:
        return self.value[0]


@unique
class ParamStyle(Enum):
    matrix = 'matrix'
    label = 'label'
    form = 'form'
    simple = 'simple'
    spaceDelimited = 'spaceDelimited'
    pipeDelimited = 'pipeDelimited'
    deepObject = 'deepObject'


@dataclass(frozen=True)
class Param:
    name: str
    """Name on python side"""
    alias: str
    """Name on OpenAPI side"""
    location: ParamLocation
    type: Type

    style: ParamStyle
    explode: bool


def get_param_model(model_: Union[openapi.Parameter, openapi.Reference], op: openapi.Operation, module: ModulePath, resolve: ResolverFunc) -> Param:
    if isinstance(model_, openapi.Reference):
        model, module, _ = resolve(model_, openapi.Parameter)
    else:
        model = cast(openapi.Parameter, model_)

    return _get_param_model(model, op, module, resolve)


def default_explode(style: ParamStyle) -> bool:
    return style is ParamStyle.form


def _get_param_model(model: openapi.Parameter, parent_op: openapi.Operation, module: ModulePath, resolve: ResolverFunc) -> Param:
    assert parent_op.operationId

    location = ParamLocation[model.in_]
    style = ParamStyle[model.style] if model.style else default_style[location]

    return Param(
        name=get_param_python_name(model),
        alias=model.name,
        location=location,
        type=get_param_type(model, parent_op.operationId, module, resolve).resolve() if model.schema_ else type(Any),
        style=style,
        explode=model.explode or default_explode(style),
    )


def get_param_type(
        param: openapi.Parameter, op_id: str, module_: ModulePath, resolve: ResolverFunc
) -> TypeHint:
    if isinstance(param.schema_, openapi.Reference):
        schema, module, schema_name = resolve(param.schema_, openapi.Schema)
    else:
        schema = param.schema_
        param_name = param.effective_name
        schema_name = param_name
        module = module_ / PARAM_MODEL

    return get_type_hint(schema, module, schema_name, param.required, resolve)


default_style = {
    ParamLocation.cookie: ParamStyle.form,
    ParamLocation.header: ParamStyle.simple,
    ParamLocation.path: ParamStyle.simple,
    ParamLocation.query: ParamStyle.form,
}
