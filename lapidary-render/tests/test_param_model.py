import unittest

import yaml
from lapidary.runtime import openapi
from lapidary.runtime.model.type_hint import TypeHint
from lapidary.runtime.module_path import ModulePath

from lapidary.render.model.param_model_class import get_param_model_classes

module_path = ModulePath('test')


class ParamModelTestCase(unittest.TestCase):
    def test_nested_schema(self):
        text = """
openapi: '3.0.3'
info:
    title: Lapidary test schema
    version: 1.0.0
paths:
    /:
        get:
            operationId: testOp
            parameters:
            - name: param
              in: query
              schema:
                type: object
                additionalProperties: false
                properties:
                    property:
                        type: string
                required:
                - property
              required: true
            responses: {}
        """

        model = openapi.OpenApiModel.parse_obj(yaml.safe_load(text))
        classes = list(get_param_model_classes(model.paths['/'].get, module_path, None))
        self.assertEqual(TypeHint.from_str('test.TestOpParam'), classes[1].attributes[0].annotation.type)
