import enum
from dataclasses import dataclass, field
from typing import Optional

from .attribute import AttributeModel
from .type_hint import TypeHint


class ModelType(enum.Enum):
    model = 'model'
    param_model = 'param_model'
    exception = 'exception'
    enum = 'enum'


@dataclass(frozen=True)
class SchemaClass:
    class_name: str
    base_type: TypeHint

    allow_extra: bool = False
    has_aliases: bool = False
    docstr: Optional[str] = None
    attributes: list[AttributeModel] = field(default_factory=list)
    model_type: ModelType = ModelType.model
