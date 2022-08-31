from dataclasses import dataclass

from .operation_function import OperationFunctionModel, get_methods
from ...openapi import model as openapi


@dataclass(frozen=True)
class ClientClass:
    methods: list[OperationFunctionModel]


def get_client_class(openapi_model: openapi.OpenApiModel) -> ClientClass:
    return ClientClass(
        methods=get_methods(openapi_model),
    )
