from dataclasses import dataclass, field
from typing import Union, Generator

from .operation_function import OperationFunctionModel, get_operation_func
from .refs import ResolverFunc
from ..module_path import ModulePath
from ...openapi import model as openapi


@dataclass(frozen=True)
class ClientClass:
    methods: list[OperationFunctionModel] = field(default_factory=list)


def get_client_class(openapi_model: openapi.OpenApiModel, module: ModulePath, resolver: ResolverFunc) -> ClientClass:
    functions = [
        get_operation_func(op, method, url_path, module / 'paths' / op.operationId, resolver)
        for url_path, path_item in openapi_model.paths.__root__.items()
        for method, op in get_operations(path_item, True)
    ]

    return ClientClass(
        methods=functions
    )


def get_operations(path_item: openapi.PathItem, skip_reference=False) -> Generator[tuple[str, Union[openapi.Operation, openapi.Reference]], None, None]:
    for op_name in path_item.__fields_set__:
        v = getattr(path_item, op_name)
        if (
                isinstance(v, openapi.Operation)
                or (not skip_reference and isinstance(v, openapi.Reference))
        ):
            yield op_name, v
