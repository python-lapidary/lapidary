import unittest

import yaml

from lapidary.openapi import model as openapi
from lapidary.render.elems import get_client_class
from lapidary.render.elems.param_model_class import get_param_model_classes
from lapidary.render.elems.type_hint import TypeHint
from lapidary.render.module_path import ModulePath

module_path = ModulePath('test')


class ParamModelTestCase(unittest.TestCase):
    def test_param_model_name_eq_type_hint(self):
        model = openapi.OpenApiModel(
            openapi='3.0.3',
            info=openapi.Info(title='Lapidary test schema', version='1.0.0'),
            paths=openapi.Paths(__root__={
                '/': openapi.PathItem(
                    get=openapi.Operation(
                        operationId='get_simple_response',
                        responses=openapi.Responses(__root__={
                            '200': openapi.Response(
                                description='test response',
                                content={'application/json': openapi.MediaType(
                                    schema=openapi.Schema(type=openapi.Type.string),
                                )}
                            )
                        }),
                        parameters=[openapi.Parameter(
                            name='key',
                            in_='query',
                            schema_=openapi.Schema(type=openapi.Type.string),
                        )],
                    ),
                ),
            }),
        )
        client_class_model = get_client_class(model, module_path, None)
        ctor_class_name = \
            [c for c in get_param_model_classes(model.paths.__root__['/'].get, ModulePath('alice'), None)][0].class_name

        self.assertEqual(ctor_class_name, client_class_model.methods[0].params_model_name.name)

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
        classes = list(get_param_model_classes(model.paths.__root__['/'].get, module_path, None))
        print(classes)
        self.assertEqual(TypeHint.from_str('test.TestOpParam'), classes[1].attributes[0].annotation.type)
