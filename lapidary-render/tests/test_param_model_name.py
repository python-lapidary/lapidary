import unittest

from lapidary.openapi import model as openapi
from lapidary.render.elems import get_client_class
from lapidary.render.elems.param_model_class import get_param_model_classes
from lapidary.render.module_path import ModulePath


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
        client_class_model = get_client_class(model, ModulePath('alice'), None)
        ctor_class_name = \
        [c for c in get_param_model_classes(model.paths.__root__['/'].get, ModulePath('alice'), None)][0].class_name

        self.assertEqual(ctor_class_name, client_class_model.methods[0].params_model_name.name)
