import enum
import unittest
from typing import Annotated

import pydantic

from lapidary.runtime import ParamLocation
from lapidary.runtime.request import get_path


class PathTestCase(unittest.TestCase):
    def test_enum_param(self):
        class MyEnum(enum.Enum):
            entry = 'value'

        class ParamModel(pydantic.BaseModel):
            p_param: Annotated[MyEnum, pydantic.Field(alias='param', in_=ParamLocation.path)]

            class Config(pydantic.BaseConfig):
                # use_enum_values = True
                allow_population_by_field_name = True

        param_model = ParamModel(
            p_param=MyEnum.entry
        )

        path = get_path('{p_param}', param_model)
        self.assertEqual('value', path)
