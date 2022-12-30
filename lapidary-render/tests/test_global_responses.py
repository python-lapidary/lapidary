import unittest

from lapidary.runtime import openapi
from lapidary.runtime.model.refs import get_resolver
from lapidary.runtime.model.type_hint import TypeHint
from lapidary.runtime.module_path import ModulePath

from lapidary.render.model.client_module import get_client_class_module


class GlobalResponsesTest(unittest.TestCase):
    def test_ref_global_responses_in_output_model(self):
        model = openapi.OpenApiModel(
            openapi='3.0.3',
            info=openapi.Info(
                title='',
                version=''
            ),
            paths=openapi.Paths(),
            components=openapi.Components(
                schemas={
                    'GSMTasksError': openapi.Schema(
                        type=openapi.Type.object,
                        properties={
                            'detail': openapi.Schema(
                                type=openapi.Type.string,
                            )
                        },
                        required=['detail'],
                    )
                },
                responses={
                    'error-response': openapi.Response(
                        description='Client error',
                        content={
                            'application/json; version=2.3.5': openapi.MediaType(
                                schema=openapi.Reference(ref='#/components/schemas/GSMTasksError'),
                            )
                        },
                    )
                },
            ),
            lapidary_responses_global=openapi.Responses(**{
                '4XX': openapi.Reference(ref='#/components/responses/error-response'),
                '5XX': openapi.Reference(ref='#/components/responses/error-response'),
            })
        )

        module_path = ModulePath('test')
        module = get_client_class_module(model, module_path / 'client.py', module_path, get_resolver(model, 'test'))
        # pp(dataclasses.asdict(module))

        expected = {
            TypeHint(module='test.components.schemas.gsm_tasks_error', name='GSMTasksError'),
        }

        self.assertEqual(expected, module.body.init_method.response_types)

    def test_inline_global_responses_in_output_model(self):
        model = openapi.OpenApiModel(
            openapi='3.0.3',
            info=openapi.Info(
                title='',
                version=''
            ),
            paths=openapi.Paths(),
            components=openapi.Components(
                schemas={
                    'GSMTasksError': openapi.Schema(
                        type=openapi.Type.object,
                        properties={
                            'detail': openapi.Schema(
                                type=openapi.Type.string,
                            )
                        },
                        required=['detail'],
                    )
                }
            ),
            lapidary_responses_global=openapi.Responses(**{
                '4XX': openapi.Response(
                    description='Client error',
                    content={
                        'application/json; version=2.3.5': openapi.MediaType(
                            schema=openapi.Reference(ref='#/components/schemas/GSMTasksError'),
                        )
                    }
                ),
                '5XX': openapi.Response(
                    description='Server error',
                    content={
                        'application/json; version=2.3.5': openapi.MediaType(
                            schema=openapi.Reference(ref='#/components/schemas/GSMTasksError'),
                        )
                    }
                ),
            })
        )

        module_path = ModulePath('test')
        module = get_client_class_module(model, module_path / 'client.py', module_path, get_resolver(model, 'test'))
        # pp(dataclasses.asdict(module))

        expected = {
            TypeHint(module='test.components.schemas.gsm_tasks_error', name='GSMTasksError'),
        }

        self.assertEqual(expected, module.body.init_method.response_types)

    def test_global_responses_as_dict(self):
        model = openapi.OpenApiModel(**{
            'openapi': '3.0.3',
            'info': openapi.Info(
                title='',
                version=''
            ),
            'paths': openapi.Paths(),
            'components': openapi.Components(
                schemas={
                    'GSMTasksError': openapi.Schema(
                        type=openapi.Type.object,
                        properties={
                            'detail': openapi.Schema(
                                type=openapi.Type.string,
                            )
                        },
                        required=['detail'],
                    )
                }
            ),
            'x-lapidary-responses-global': openapi.Responses(**{
                '4XX': openapi.Response(
                    description='Client error',
                    content={
                        'application/json; version=2.3.5': openapi.MediaType(
                            schema=openapi.Reference(ref='#/components/schemas/GSMTasksError'),
                        )
                    }
                ),
                '5XX': openapi.Response(
                    description='Server error',
                    content={
                        'application/json; version=2.3.5': openapi.MediaType(
                            schema=openapi.Reference(ref='#/components/schemas/GSMTasksError'),
                        )
                    }
                ),
            })
        })

        module_path = ModulePath('test')
        module = get_client_class_module(model, module_path / 'client.py', module_path, get_resolver(model, 'test'))

        expected = {
            TypeHint(module='test.components.schemas.gsm_tasks_error', name='GSMTasksError'),
        }

        self.assertEqual(expected, module.body.init_method.response_types)
