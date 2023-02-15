import unittest

from lapidary.runtime import openapi
from lapidary.runtime.model import get_resolver, get_client_model
from lapidary.runtime.module_path import ModulePath

oa_model = openapi.OpenApiModel(
    openapi='3.0.3',
    info=openapi.Info(
        title='',
        version=''),
    components=openapi.Components(
        schemas=dict(
            damian=openapi.Schema(type=openapi.Type.integer),
        )
    ),
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
                    ),
                    openapi.Parameter(
                        name="param_b",
                        in_=openapi.In1.query.value,
                        schema=openapi.Schema(
                            type=openapi.Type.object,
                            properties={
                                "prop_ba": openapi.Schema(type=openapi.Type.string),
                                "prop_bb": openapi.Reference(ref="#/components/schemas/damian")
                            }
                        )
                    ),
                ],
                responses=openapi.Responses(**dict(default=openapi.Response(description='no response'))),
            )
        )
    })
)


class ParamModelTest(unittest.TestCase):
    def test_type(self):
        model = get_client_model(oa_model, ModulePath('test_module'), get_resolver(oa_model, 'test_module'))
        param = model.methods['my_op'].params[0]
        self.assertEqual('my_param_q', param.name)
        self.assertEqual('myParam', param.alias)
        import test_module.ops.my_op.parameters as pm
        self.assertEqual(pm.my_param, param.type)
