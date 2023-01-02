import logging
import warnings
from dataclasses import dataclass
from typing import Optional, Union

from lapidary.runtime import openapi
from lapidary.runtime.model.params import ParamPlacement
from lapidary.runtime.model.refs import ResolverFunc
from lapidary.runtime.model.type_hint import TypeHint, resolve_type_hint, get_type_hint, GenericTypeHint
from lapidary.runtime.module_path import ModulePath
from lapidary.runtime.names import PARAM_MODEL, RESPONSE_BODY, get_subtype_name, maybe_mangle_name, response_type_name

from .attribute import AttributeModel
from .attribute_annotation import AttributeAnnotationModel
from .request_body import get_request_body_type

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OperationFunctionModel:
    name: str
    request_type: Optional[TypeHint]
    params: list[AttributeModel]
    response_type: Optional[TypeHint]
    auth_name: Optional[str]
    docstr: Optional[str] = None


_FIELD_PROPS = dict(
    in_=None,
    description=None,
    allowEmptyValue=False,
    style=None,
    explode=None,
    allowReserved=False,
)


def get_operation_param(
        param: Union[openapi.Parameter, openapi.Reference], parent_name: str, module: ModulePath, resolve: ResolverFunc
) -> AttributeModel:
    try:
        return get_operation_param_(param, parent_name, module, resolve)
    except:
        logger.warning("Error while handling parameter %s/%s", parent_name, param.name)
        raise


def get_operation_param_(
        param: Union[openapi.Parameter, openapi.Reference], parent_name: str, module: ModulePath, resolve: ResolverFunc
) -> AttributeModel:
    if isinstance(param, openapi.Reference):
        param, module, _ = resolve(param, openapi.Parameter)

    schema = param.schema_
    if isinstance(schema, openapi.Reference):
        schema, module, schema_name = resolve(schema, openapi.Schema)
    else:
        param_name = param.lapidary_name or param.name
        schema_name = get_subtype_name(parent_name, param_name)
        module = module / PARAM_MODEL

    field_props = {k: (getattr(param, k) or _FIELD_PROPS[k]) for k in _FIELD_PROPS}
    param_name = param.in_[0] + '_' + maybe_mangle_name(param.lapidary_name or param.name, False)

    return AttributeModel(
        name=param_name,
        annotation=AttributeAnnotationModel(
            type=get_type_hint(schema, module, schema_name, param.required, resolve),
            field_props=field_props,
        ),
        deprecated=param.deprecated,
        required=param.required,
    )


def get_operation_func(
        op: openapi.Operation, root: ModulePath, operation_id: Optional[str], resolver: ResolverFunc
) -> OperationFunctionModel:
    if not operation_id:
        raise ValueError('operationId is required')

    module = root / 'paths' / op.operationId

    params = []
    if op.parameters:
        for oapi_param in op.parameters:
            if oapi_param.in_ == ParamPlacement.header.value and oapi_param.name.lower() in [
                'accept', 'content-type', 'authorization'
            ]:
                warnings.warn(f'Header param "{oapi_param.name}" ignored')
                continue
            params.append(get_operation_param(oapi_param, op.operationId, module, resolver))

    request_type = get_request_body_type(op, module, resolver) if op.requestBody else None

    response_types = get_response_types(op, module, resolver)
    if len(response_types) == 0:
        response_type = None
    elif len(response_types) == 1:
        response_type = response_types.pop()
    else:
        response_type = GenericTypeHint.union_of(tuple(response_types))

    auth_name = None
    if op.security is not None and len(op.security) > 0:
        requirement = next(iter(op.security)).__root__
        if len(requirement) > 0:
            auth_name = next(iter(requirement.keys()))

    return OperationFunctionModel(
        name=op.operationId,
        request_type=request_type,
        params=params,
        response_type=response_type,
        auth_name=auth_name,
    )


def get_response_types(op: openapi.Operation, module: ModulePath, resolve: ResolverFunc) -> set[TypeHint]:
    """
    Generate unique collection of types that may be returned by the operation. Skip types that are marked as exceptions as those are raised instead.
    """

    return get_response_types_(op.operationId, op.responses, module, resolve)


def get_response_types_(op_name: Optional[str], responses: openapi.Responses, module: ModulePath, resolve: ResolverFunc) -> set[TypeHint]:
    response_types = set()
    for resp_code, response in responses.items():
        if isinstance(response, openapi.Reference):
            response, module, name = resolve(response, openapi.Response)
        if response.content is None:
            continue
        for media_type in response.content.values():
            schema = media_type.schema_
            if isinstance(schema, openapi.Reference):
                schema, resp_module, name = resolve(schema, openapi.Schema)
            else:
                name = response_type_name(op_name, resp_code)
                resp_module = module / RESPONSE_BODY
            if schema.lapidary_model_type is openapi.LapidaryModelType.exception:
                continue
            typ = resolve_type_hint(schema, resp_module, name, resolve)

            if schema.lapidary_model_type is openapi.LapidaryModelType.iterator:
                typ = to_iterator(typ)

            response_types.add(typ)
    return response_types


def to_iterator(type_: TypeHint) -> TypeHint:
    if not isinstance(type_, GenericTypeHint):
        return type_

    if type_.origin == TypeHint.from_type(Union):
        return GenericTypeHint.union_of(tuple(to_iterator(targ) for targ in type_.args))

    if type_.origin == TypeHint.from_type(list):
        return GenericTypeHint(module='collections.abc', name='Iterator', args=type_.args)

    return type_
