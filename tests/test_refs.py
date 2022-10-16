from unittest import TestCase

from lapidary.openapi import model as openapi
from lapidary.render.elems.refs import resolve
from lapidary.render.elems.type_hint import TypeHint, get_type_hint
from lapidary.render.module_path import ModulePath

schema_carol = openapi.Schema()
schema_bob = openapi.Schema(properties={'carol': schema_carol})
model = openapi.OpenApiModel(
    openapi='3.0.3',
    info=openapi.Info(title='', version=''),
    paths=openapi.Paths(__root__={}),
    components=openapi.Components(
        schemas={
            'alice': openapi.Reference(**{'$ref': '#/components/schemas/bob'}),
            'bob': schema_bob,

            'joker': openapi.Reference(**{'$ref': '#/components/schemas/joker'}),

            'batman': openapi.Reference(**{'$ref': '#/components/schemas/robin'}),
            'robin': openapi.Reference(**{'$ref': '#/components/schemas/batman'}),

            'charlie': openapi.Schema(oneOf=[
                openapi.Schema()
            ]),
        }
    )
)


class ReferenceTest(TestCase):
    def test_resolve_ref(self):
        self.assertEqual(
            resolve(model, 'root', openapi.Reference(**{'$ref': '#/components/schemas/alice'}), openapi.Schema),
            (schema_bob, ModulePath('root.components.schemas.bob'), 'bob')
        )

    def test_nested_schema(self):
        self.assertEqual(
            resolve(model, 'root', openapi.Reference(**{'$ref': '#/components/schemas/bob/properties/carol'}), openapi.Schema),
            (schema_carol, ModulePath('root.components.schemas.bob.properties.carol'), 'carol')
        )

    def test_direct_recursion_fails(self):
        def raises():
            resolve(model, 'root', openapi.Reference(**{'$ref': '#/components/schemas/joker'}), openapi.Schema)

        self.assertRaises(RecursionError, raises)

    def test_indirect_recursion_fails(self):
        def raises():
            resolve(model, 'root', openapi.Reference(**{'$ref': '#/components/schemas/batman'}), openapi.Schema)

        self.assertRaises(RecursionError, raises)

    def test_empty_schema_generate_any_type_ref(self):
        type_ref = get_type_hint(openapi.Schema(), ModulePath('lapidary_test'), 'empty_schema', True, None)
        self.assertEqual(type_ref, TypeHint.from_str('typing.Any'))
