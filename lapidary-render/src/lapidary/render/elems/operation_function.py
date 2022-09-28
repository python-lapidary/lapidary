import logging
import re
from dataclasses import dataclass
from typing import Optional, Union

import inflection

from .attribute import AttributeModel
from .attribute_annotation import AttributeAnnotationModel
from .client_func_response_map import get_response_map
from .modules import PARAM_MODEL
from .refs import ResolverFunc
from .request_body import get_request_body_type
from .response_body import response_type_name
from ..module_path import ModulePath
from ..type_ref import TypeRef, get_type_ref, GenericTypeRef, resolve_type_ref
from ...openapi import model as openapi
from ...openapi.model import LapidaryModelType

RESPONSE_BODY = 'response_body'

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OperationFunctionModel:
    name: str
    method: str
    path: str
    request_type: Optional[TypeRef]
    params: list[AttributeModel]
    params_model_name: Optional[TypeRef]
    response_map: dict[str, dict[str, TypeRef]]
    response_type: Optional[TypeRef]
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


def get_operation_param(param: Union[openapi.Parameter, openapi.Reference], parent_name: str, module: ModulePath, resolve: ResolverFunc) -> AttributeModel:
    if isinstance(param, openapi.Reference):
        param, module, _ = resolve(param, openapi.Parameter)

    schema = param.schema_
    if isinstance(schema, openapi.Reference):
        schema, module, schema_name = resolve(schema, openapi.Schema)
    else:
        schema_name = inflection.camelize(parent_name) + inflection.camelize(param.name)
        module = module / PARAM_MODEL

    field_props = {k: (getattr(param, k) or _FIELD_PROPS[k]) for k in _FIELD_PROPS}
    param_name = param.in_[0] + '_' + sanitise_param_name(param.name)

    return AttributeModel(
        name=param_name,
        annotation=AttributeAnnotationModel(
            type=get_type_ref(schema, module, schema_name, param.required, resolve),
            field_props=field_props,
        ),
        deprecated=param.deprecated,
        required=param.required,
    )


def sanitise_param_name(param_name: str) -> str:
    # potential name clash
    return re.compile(r'\W+').sub('_', param_name)


def get_operation_func(op: openapi.Operation, method: str, url_path: str, module: ModulePath, resolver: ResolverFunc) -> OperationFunctionModel:
    params = [get_operation_param(oapi_param, op.operationId, module, resolver) for oapi_param in op.parameters] if op.parameters else []

    request_type = get_request_body_type(op, module, resolver) if op.requestBody else None

    response_map = get_response_map(
        op.responses,
        op.operationId,
        module,
        resolver
    )

    response_types = get_response_types(op, module, resolver)
    if len(response_types) == 0:
        response_type = None
    elif len(response_types) == 1:
        response_type = response_types.pop()
    else:
        response_type = GenericTypeRef.union_of(list(response_types))

    auth_name = None
    if op.security is not None and len(op.security) > 0:
        requirement = next(iter(op.security)).__root__
        if len(requirement) > 0:
            auth_name = next(iter(requirement.keys()))

    return OperationFunctionModel(
        name=op.operationId,
        method=method,
        path=re.compile(r'\{([^}]+)\}').sub(r'{p_\1}', url_path),
        request_type=request_type,
        params=params,
        params_model_name=TypeRef(module=(module / PARAM_MODEL).str(), name=inflection.camelize(op.operationId)) if op.parameters else None,
        response_map=response_map,
        response_type=response_type,
        auth_name=auth_name,
    )


def get_response_types(op: openapi.Operation, module: ModulePath, resolve: ResolverFunc) -> set[TypeRef]:
    """
    Generate unique collection of types that may be returned by the operation. Skip types that are marked as exceptions as those are raised instead.
    """
    response_types = set()
    for resp_code, response in op.responses.__root__.items():
        if response.content is None:
            continue
        for media_type in response.content.values():
            schema = media_type.schema_
            if isinstance(schema, openapi.Reference):
                schema, resp_module, name = resolve(schema, openapi.Schema)
            else:
                name = response_type_name(op, resp_code)
                resp_module = module / RESPONSE_BODY
            if schema.lapidary_model_type is LapidaryModelType.exception:
                continue
            typ = resolve_type_ref(schema, resp_module, name, resolve)
            response_types.add(typ)
    return response_types
