from dataclasses import dataclass

from .operation_function import OperationFunctionModel, get_path_op_funcs
from ..refs import ResolverFunc
from ...openapi import model as openapi


@dataclass(frozen=True)
class ClientClass:
    methods: list[OperationFunctionModel]


def get_client_class(openapi_model: openapi.OpenApiModel, package: str, resolver: ResolverFunc) -> ClientClass:
    functions = []
    for url_path, path_item in openapi_model.paths.__root__.items():
        for op in get_path_op_funcs(path_item, [package, 'paths', url_path], resolver):
            functions.append(op)

    return ClientClass(
        methods=functions
    )
