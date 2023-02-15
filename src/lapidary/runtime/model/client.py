import collections.abc
from dataclasses import dataclass, field
from typing import Mapping, Optional, Union, List, Tuple, Dict, Any

from .op import OperationModel, get_operation_functions
from .refs import ResolverFunc
from .response_map import ResponseMap, get_api_responses
from ..module_path import ModulePath
from ..openapi import model as openapi


@dataclass(frozen=True)
class ClientModel:
    auth_models: Mapping[str, Any] = field(default_factory=dict)
    base_url: Optional[str] = None
    default_auth: Optional[str] = None
    headers: List[Tuple[str, str]] = field(default_factory=list)
    methods: Mapping[str, OperationModel] = field(default_factory=dict)
    response_map: ResponseMap = field(default_factory=dict)


def get_client_model(openapi_model: openapi.OpenApiModel, module: ModulePath, resolve: ResolverFunc) -> ClientModel:
    default_auth = next(iter(openapi_model.security[0].__root__.keys())) if openapi_model.security else None

    base_url = (
        openapi_model.servers[0].url if openapi_model.servers and openapi_model.servers
        else None
    )

    auth_models = (
        openapi_model.components.securitySchemes
        if openapi_model.components and openapi_model.components.securitySchemes
        else {}
    )

    api_responses = get_api_responses(openapi_model, module) if openapi_model.lapidary_responses_global else {}
    return ClientModel(
        base_url=base_url,
        headers=get_global_headers(openapi_model.lapidary_headers_global),
        default_auth=default_auth,
        response_map=api_responses,
        auth_models=auth_models,
        methods=get_operation_functions(openapi_model, module, resolve),
    )


def get_global_headers(global_headers: Optional[Union[
    Dict[str, Union[str, List[str]]],
    List[Tuple[str, str]]
]]) -> List[Tuple[str, str]]:
    """Normalize headers structure"""
    if global_headers is None:
        return []

    result_headers = []
    input_header_list = global_headers.items() if isinstance(global_headers, Mapping) else global_headers
    for key, values in input_header_list:
        if not isinstance(values, collections.abc.Collection) or isinstance(values, str):
            values = [values]
        for value in values:
            result_headers.append((key, value,))

    return result_headers
