import unittest

from lapidary.runtime import openapi
from lapidary.runtime.model import get_resolver, get_client_model
from lapidary.runtime.module_path import ModulePath


class ParamModelTest(unittest.TestCase):
    def test_type(self):
        oa_model = openapi.OpenApiModel(
            openapi='3.0.3',
            info=openapi.Info(title='', version=''),
            paths=openapi.Paths(**{
                '/': openapi.PathItem(
                    get=openapi.Operation(
                        operationId='my_op',
                        parameters=[
                            openapi.Parameter(
                                name='myParam',
                                in_='query',
                                required=True,
                                schema=openapi.Schema(
                                    type='object',
                                    required=['myProp'],
                                    properties=dict(
                                        myProp=openapi.Schema(type='string')
                                    ),
                                    additionalProperties=False,
                                ),
                                lapidary_name='my_param'
                            )
                        ],
                        responses=openapi.Responses(**dict(default=openapi.Response(description='no response'))),
                    )
                )
            })
        )

        model = get_client_model(oa_model, ModulePath('test_module'), get_resolver(oa_model, 'test_module'))
        param = model.methods['my_op'].params[0]
        self.assertEqual('q_my_param', param.name)
        self.assertEqual('myParam', param.alias)
        import test_module.paths.my_op.param_model as pm
        self.assertEqual(pm.MyOpMyParam, param.type)
