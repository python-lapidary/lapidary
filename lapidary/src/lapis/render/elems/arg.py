from dataclasses import dataclass
from typing import Optional

from lapis_client_base import ParamDirection


@dataclass(frozen=True)
class ArgModel:
    name: str
    annotation: str

    deprecated = False
    style: Optional[str] = None
    explode: Optional[bool] = None
    direction: ParamDirection = ParamDirection.read | ParamDirection.write
    allowReserved: Optional[bool] = False
