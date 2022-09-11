import typing
from unittest import TestCase

import lapis_client_base
import pydantic
from lapis_client_base import Absent

from lapis.openapi import model as openapi
from lapis.render.elems.attribute import AttributeModel
from lapis.render.elems.attribute_annotation import AttributeAnnotationModel
from lapis.render.elems.schema_class import get_schema_class, SchemaClass
from lapis.render.elems.type_ref import TypeRef, GenericTypeRef, BuiltinTypeRef
from lapis.render.module_path import ModulePath
from lapis.render.refs import get_resolver

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
                    field_props={'default': 'lapis_client_base.absent.ABSENT'},
                    direction=None,
                    style=None,
                    explode=None,
                    allowReserved=False),
                deprecated=False
            )]
        )

        self.assertEqual(schema, a)
