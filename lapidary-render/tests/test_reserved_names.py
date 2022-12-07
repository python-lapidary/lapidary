from unittest import TestCase

from lapidary.runtime import openapi
from lapidary.runtime.module_path import ModulePath

from lapidary.render.model.schema_class import get_schema_classes


class ReeservedNamesTest(TestCase):
    def test_keyword_property(self):
        model = openapi.Schema(
            type=openapi.Type.object,
            properties={
                'async': openapi.Schema(
                    type=openapi.Type.string
                )
            }
        )

        classes = [c for c in get_schema_classes(model, 'SchemaModel', ModulePath('test'), None)]
        self.assertEqual('async_', classes[0].attributes[0].name)

    def test_builtin_property(self):
        model = openapi.Schema(
            type=openapi.Type.object,
            properties={
                'str': openapi.Schema(
                    type=openapi.Type.string
                )
            }
        )

        classes = [c for c in get_schema_classes(model, 'SchemaModel', ModulePath('test'), None)]
        self.assertEqual('str', classes[0].attributes[0].name)

    def test_keyword_enum_value(self):
        model = openapi.Schema(
            type=openapi.Type.string,
            enum=['async']
        )

        classes = [c for c in get_schema_classes(model, 'SchemaModel', ModulePath('test'), None)]
        self.assertEqual('async_', classes[0].attributes[0].name)

    def test_builtin_eum_value(self):
        model = openapi.Schema(
            type=openapi.Type.string,
            enum=['str']
        )

        classes = [c for c in get_schema_classes(model, 'SchemaModel', ModulePath('test'), None)]
        self.assertEqual('str', classes[0].attributes[0].name)
