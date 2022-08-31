from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class OperationFunctionModel:
    function_name: str
    params: dict[str, str]
    params_model_name: Optional[str]
    result_class_name: str
    docstr: Optional[str]


def get_methods(openapi_model) -> list[OperationFunctionModel]:
    return []
