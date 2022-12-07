import enum
from dataclasses import dataclass, field
from typing import Optional

from lapidary.runtime.model.type_hint import TypeHint

from ..model.attribute import AttributeModel


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
