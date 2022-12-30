from unittest import TestCase

from lapidary.runtime import Absent, openapi
from lapidary.runtime.model.refs import get_resolver
from lapidary.runtime.model.type_hint import BuiltinTypeHint, TypeHint
from lapidary.runtime.module_path import ModulePath

from lapidary.render.model.attribute import AttributeModel
from lapidary.render.model.attribute_annotation import AttributeAnnotationModel
from lapidary.render.model.schema_class import get_schema_class, get_schema_classes
from lapidary.render.model.schema_class_model import SchemaClass

model = openapi.OpenApiModel(
    openapi='3.0.3',
    info=openapi.Info(title='', version=''),
    paths=openapi.Paths(),
    components=openapi.Components(
        schemas={
            'alice': openapi.Schema(
                type=openapi.Type.object,
                properties={
                    'bob': openapi.Schema(
                        type=openapi.Type.string
                    )
                },
                additionalProperties=False,
            ),
            'charlie': openapi.Schema(
                oneOf=[
                    openapi.Schema(
                        type=openapi.Type.object,
                        lapidary_name='FirstSchemaClass',
                        properties={
                            'a': openapi.Schema()
                        },
                    ),
                    openapi.Schema(
                        lapidary_name='SecondSchemaClass',
                        type=openapi.Type.object,
                        properties={
                            'a': openapi.Schema()
                        },
                    ),
                ]
            )
        }
    )
)


class Test(TestCase):
    def test_resolve_ref(self):
        a = get_schema_class(
            model.components.schemas['alice'],
            'alice',
            ModulePath('alice'),
            get_resolver(model, 'bob'),
        )
        schema = SchemaClass(
            class_name='alice',
            base_type=TypeHint.from_str('pydantic.BaseModel'),
            docstr=None,
            attributes=[AttributeModel(
                name='bob',
                annotation=AttributeAnnotationModel(
                    type=BuiltinTypeHint.from_type(str).union_with(TypeHint.from_type(Absent)),
                    field_props={},
                    style=None,
                    explode=None,
                    allowReserved=False,
                    default='lapidary.runtime.absent.ABSENT',
                ),
                deprecated=False
            )]
        )

        self.assertEqual(schema, a)

    def test_schema_type_name(self):
        classes = [cls for cls in get_schema_classes(
            model.components.schemas['charlie'],
            'alice',
            ModulePath('test'),
            get_resolver(model, 'test'),
        )]
        class_names = [cls.class_name for cls in classes]
        self.assertEqual(class_names, ['FirstSchemaClass', 'SecondSchemaClass'])
