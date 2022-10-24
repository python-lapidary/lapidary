import logging
from unittest import TestCase

import yaml
from lapidary.openapi import model as openapi
from lapidary.render.elems.attribute import AttributeModel
from lapidary.render.elems.attribute_annotation import AttributeAnnotationModel
from lapidary.render.elems.refs import get_resolver
from lapidary.render.elems.schema_class_model import SchemaClass
from lapidary.render.elems.schema_module import SchemaModule, get_schema_module
from lapidary.render.elems.type_hint import TypeHint
from lapidary.render.module_path import ModulePath
from lapidary.render.schema import get_schema_modules

logging.getLogger('lapidary').setLevel(logging.DEBUG)

schema = """
openapi: '3.0.3'
info:
    title: Lapidary test schema
    version: 1.0.0
paths: {}
components:
    schemas:
        NonSpaceName:
            additionalProperties: false
            type: object
            properties:
                random property:
                    type: object
                    additionalProperties: false
                    properties:
                        key:
                            type: string
                    required: 
                    - key
            required: 
            - random property
            x-lapidary-names:
                random property: random_property
"""

schema_with_space = """
openapi: '3.0.3'
info:
    title: Lapidary test schema
    version: 1.0.0
paths: {}
components:
    schemas:
        random name:
            type: object
            properties:
                key:
                    type: string
"""

sub_schema_with_space = """
openapi: '3.0.3'
info:
    title: Lapidary test schema
    version: 1.0.0
paths: {}
components:
    schemas:
        Alice:
            type: object
            properties:
                random name:
                    type: object
                    properties:
                        key:
                            type: string
"""

operation_param_with_space = """
openapi: '3.0.3'
info:
    title: Lapidary test schema
    version: 1.0.0
paths:
    /:
        get:
            operationId: testOp
            parameters:
            - name: test param
              in: query
              schema:
                type: string
            responses: 
              default:
                description: ''
                content:
                  application/json:
                    schema:
                      type: string
"""


class NamingTest(TestCase):
    def test_name_with_alias(self):
        model = openapi.OpenApiModel.parse_obj(yaml.safe_load(schema))
        resolve = get_resolver(model, 'lapidary_test')
        module_path = ModulePath('lapidary_test')

        expected = SchemaModule(
            path=module_path,
            imports=[
            ],
            body=[
                SchemaClass(
                    class_name='NonSpaceNameRandomProperty',
                    base_type=TypeHint.from_str('pydantic.BaseModel'),
                    attributes=[
                        AttributeModel(
                            'key',
                            AttributeAnnotationModel(TypeHint.from_type(str), {}),
                        ),
                    ],
                ),
                SchemaClass(
                    has_aliases=True,
                    class_name='NonSpaceName',
                    base_type=TypeHint.from_str('pydantic.BaseModel'),
                    attributes=[
                        AttributeModel(
                            'random_property',
                            AttributeAnnotationModel(
                                TypeHint.from_str('lapidary_test.NonSpaceNameRandomProperty'),
                                {
                                    'alias': "'random property'",
                                },
                            ),
                        ),
                    ],
                ),
            ]
        )

        mod = get_schema_module(model.components.schemas['NonSpaceName'], 'NonSpaceName', module_path, resolve)
        # from pprint import pp
        # pp(mod)

        self.assertEqual(expected, mod)

    def test_name_with_space(self):
        model = openapi.OpenApiModel.parse_obj(yaml.safe_load(schema_with_space))
        resolve = get_resolver(model, 'lapidary_test')
        module_path = ModulePath('lapidary_test')

        with self.assertRaises(ValueError):
            from pprint import pp
            pp([mod for mod in get_schema_modules(model, module_path, resolve)])

    def test_subschema_name_with_space(self):
        model = openapi.OpenApiModel.parse_obj(yaml.safe_load(sub_schema_with_space))
        resolve = get_resolver(model, 'lapidary_test')
        module_path = ModulePath('lapidary_test')

        with self.assertRaises(ValueError):
            _ = [mod for mod in get_schema_modules(model, module_path, resolve)]
