import unittest

from lapidary.render.elems.client_module import get_client_class_module
from lapidary.render.elems.refs import get_resolver
from lapidary.render.elems.type_hint import TypeHint
from lapidary.render.module_path import ModulePath
from lapidary.runtime import openapi


class GlobalResponsesTest(unittest.TestCase):
    def test_ref_global_responses_in_output_model(self):
        model = openapi.OpenApiModel(
            openapi='3.0.3',
            info=openapi.Info(
                title='',
                version=''
            ),
            paths=openapi.Paths(__root__={}),
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
            lapidary_responses_global=openapi.Responses(__root__={
                '4XX': openapi.Reference(ref='#/components/responses/error-response'),
                '5XX': openapi.Reference(ref='#/components/responses/error-response'),
            })
        )

        module_path = ModulePath('test')
        module = get_client_class_module(model, module_path / 'client.py', module_path, get_resolver(model, 'test'))
        # pp(dataclasses.asdict(module))

        expected = {
            '4XX': {'application/json; version=2.3.5': TypeHint(module='test.components.schemas.gsm_tasks_error', name='GSMTasksError')},
            '5XX': {'application/json; version=2.3.5': TypeHint(module='test.components.schemas.gsm_tasks_error', name='GSMTasksError')},
        }

        self.assertEqual(expected, module.body.init_method.response_map)

    def test_inline_global_responses_in_output_model(self):
        model = openapi.OpenApiModel(
            openapi='3.0.3',
            info=openapi.Info(
                title='',
                version=''
            ),
            paths=openapi.Paths(__root__={}),
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
            lapidary_responses_global=openapi.Responses(__root__={
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
            '4XX': {'application/json; version=2.3.5': TypeHint(module='test.components.schemas.gsm_tasks_error', name='GSMTasksError')},
            '5XX': {'application/json; version=2.3.5': TypeHint(module='test.components.schemas.gsm_tasks_error', name='GSMTasksError')},
        }

        self.assertEqual(expected, module.body.init_method.response_map)

    def test_global_responses_as_dict(self):
        model = openapi.OpenApiModel(**{
            'openapi': '3.0.3',
            'info': openapi.Info(
                title='',
                version=''
            ),
            'paths': openapi.Paths(__root__={}),
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
            'x-lapidary-responses-global': openapi.Responses(__root__={
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
        # pp(dataclasses.asdict(module))

        expected = {
            '4XX': {'application/json; version=2.3.5': TypeHint(module='test.components.schemas.gsm_tasks_error', name='GSMTasksError')},
            '5XX': {'application/json; version=2.3.5': TypeHint(module='test.components.schemas.gsm_tasks_error', name='GSMTasksError')},
        }

        self.assertEqual(expected, module.body.init_method.response_map)
