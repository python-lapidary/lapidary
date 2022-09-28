from unittest import TestCase

from lapidary_base import Absent

from lapidary.openapi import model as openapi
from lapidary.render.elems.attribute import AttributeModel
from lapidary.render.elems.attribute_annotation import AttributeAnnotationModel
from lapidary.render.elems.refs import get_resolver
from lapidary.render.elems.schema_class import get_schema_class, SchemaClass, get_schema_classes
from lapidary.render.module_path import ModulePath
from lapidary.render.type_ref import TypeRef, BuiltinTypeRef

model = openapi.OpenApiModel(
    openapi='3.0.3',
    info=openapi.Info(title='', version=''),
    paths=openapi.Paths(__root__={}),
    components=openapi.Components(
        schemas={
            'alice': openapi.Schema(
                type=openapi.Type.object,
                properties={
                    'bob': openapi.Schema(
                        type=openapi.Type.string
                    )
                }
            ),
            'charlie': openapi.Schema(
                oneOf=[
                    openapi.Schema(
                        type=openapi.Type.object,
                        lapidary_type_name='FirstSchemaClass',
                        properties={
                            'a': openapi.Schema()
                        },
                    ),
                    openapi.Schema(
                        lapidary_type_name='SecondSchemaClass',
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
        a = get_schema_class(model.components.schemas['alice'], 'alice', ModulePath('alice'), get_resolver(model, 'bob'))
        schema = SchemaClass(
            class_name='alice',
            base_type=TypeRef.from_str('pydantic.BaseModel'),
            docstr=None,
            attributes=[AttributeModel(
                name='bob',
                annotation=AttributeAnnotationModel(
                    type=BuiltinTypeRef.from_type(str).union_with(TypeRef.from_type(Absent)),
                    field_props={},
                    style=None,
                    explode=None,
                    allowReserved=False,
                    default='lapidary_base.absent.ABSENT',
                ),
                deprecated=False
            )]
        )

        self.assertEqual(schema, a)

    def test_schema_type_name(self):
        classes = [cls for cls in get_schema_classes(model.components.schemas['charlie'], 'alice', ModulePath('test'), get_resolver(model, 'test'))]
        class_names = [cls.class_name for cls in classes]
        self.assertEqual(class_names, ['FirstSchemaClass', 'SecondSchemaClass'])
