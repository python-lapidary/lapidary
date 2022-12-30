import logging
from unittest import TestCase

import yaml
from lapidary.runtime import openapi
from lapidary.runtime.model.refs import get_resolver
from lapidary.runtime.model.type_hint import TypeHint
from lapidary.runtime.module_path import ModulePath

from lapidary.render.model.attribute import AttributeModel
from lapidary.render.model.attribute_annotation import AttributeAnnotationModel
from lapidary.render.model.param_model_class import get_param_model_classes
from lapidary.render.model.schema_class import get_schema_classes
from lapidary.render.model.schema_class_model import SchemaClass
from lapidary.render.model.schema_module import SchemaModule, get_schema_module
from lapidary.render.model.schema_modules import get_schema_modules

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

module_path = ModulePath('lapidary_test')


class NamingTest(TestCase):
    def test_name_with_alias(self):
        model = openapi.OpenApiModel.parse_obj(yaml.safe_load(schema))
        resolve = get_resolver(model, 'lapidary_test')

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

        self.assertEqual(expected, mod)

    def test_name_with_space(self):
        model = openapi.OpenApiModel.parse_obj(yaml.safe_load(schema_with_space))
        resolve = get_resolver(model, 'lapidary_test')

        with self.assertRaises(ValueError):
            _ = [mod for mod in get_schema_modules(model, module_path, resolve)]

    def test_null_enum(self):
        model = openapi.Schema(
            enum=[None],
            nullable=True,
        )
        with self.assertRaises(ValueError):
            _ = [c for c in get_schema_classes(model, 'test', module_path, None)]

    def test_null_enum_with_alias(self):
        model = openapi.Schema(
            enum=[None],
            nullable=True,
            lapidary_names={
                None: 'null'
            }
        )
        result = [c for c in get_schema_classes(model, 'test', module_path, None)]
        self.assertEqual('null', result[0].attributes[0].name)

    def test_param_name_with_space(self):
        schema_text = """
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
            responses: {}
        """

        model = openapi.OpenApiModel.parse_obj(yaml.safe_load(schema_text))
        param_model_class = next(get_param_model_classes(model.paths['/'].get, module_path, None))

        attr = param_model_class.attributes[0]

        self.assertEqual('q_testu_000020param', attr.name)
        self.assertEqual("'test param'", attr.annotation.field_props['alias'])
