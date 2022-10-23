from unittest import TestCase

from lapidary.openapi import model as openapi
from lapidary.render.elems.attribute import AttributeModel
from lapidary.render.elems.attribute_annotation import AttributeAnnotationModel
from lapidary.render.elems.refs import get_resolver
from lapidary.render.elems.schema_class_model import SchemaClass
from lapidary.render.elems.schema_module import SchemaModule, get_schema_module
from lapidary.render.elems.type_hint import TypeHint
from lapidary.render.module_path import ModulePath

model = openapi.OpenApiModel(
    openapi='3.0.3',
    info=openapi.Info(title='Lapidary test schema', version='1.0.0'),
    paths=openapi.Paths(__root__={}),
    components=openapi.Components(
        schemas={
            'NonSpaceName': openapi.Schema(
                additionalProperties=False,
                type=openapi.Type.object,
                properties={
                    'random property': openapi.Schema(
                        type=openapi.Type.object,
                        additionalProperties=False,
                        properties={
                            'key': openapi.Schema(
                                type=openapi.Type.string,
                            ),
                        },
                        required=['key'],
                    )
                },
                required=['random property'],
                lapidary_names={
                    'random property': 'random_property'
                },
            ),
        },
    ),
)

resolve = get_resolver(model, 'lapidary_test')
module_path = ModulePath('lapidary_test')


class OperationResponseTest(TestCase):
    def test_response_body_schema_model(self):
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
