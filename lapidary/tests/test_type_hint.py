from unittest import TestCase

from lapidary.runtime import openapi
from lapidary.runtime.model.refs import get_resolver
from lapidary.runtime.model.type_hint import GenericTypeHint, BuiltinTypeHint, get_type_hint, TypeHint
from lapidary.runtime.module_path import ModulePath

schema_carol = openapi.Schema()
schema_bob = openapi.Schema(properties={'carol': schema_carol})
model = openapi.OpenApiModel(
    openapi='3.0.3',
    info=openapi.Info(title='', version=''),
    paths=openapi.Paths(__root__={}),
    components=openapi.Components(
        schemas=dict(
            alice=openapi.Schema(oneOf=[
                openapi.Schema(type=openapi.Type.string),
                openapi.Schema(type=openapi.Type.integer),
            ]),
            bob=openapi.Schema(oneOf=[
                openapi.Reference(ref='#/components/schemas/carol'),
                openapi.Reference(ref='#/components/schemas/damian'),
            ]),
            carol=openapi.Schema(type=openapi.Type.string),
            damian=openapi.Schema(type=openapi.Type.integer),
        )
    )
)


class OneOfTypeHintTest(TestCase):
    def test_get_type_ref(self):
        self.assertEqual(
            GenericTypeHint(module='typing', name='Union', args=[
                BuiltinTypeHint(name='str'),
                BuiltinTypeHint(name='int'),
            ]),
            get_type_hint(
                model.components.schemas['alice'],
                ModulePath('mymodule'),
                'Alice',
                True,
                get_resolver(model, 'mypackage')
            )
        )

    def test_get_type_ref_references(self):
        self.assertEqual(
            GenericTypeHint(module='typing', name='Union', args=[
                BuiltinTypeHint(name='str'),
                BuiltinTypeHint(name='int'),
            ]),
            get_type_hint(
                model.components.schemas['bob'],
                ModulePath('mymodule'),
                'Bob',
                True,
                get_resolver(model, 'mypackage')
            )
        )

    def test_resolve(self):
        print(TypeHint.from_str('lapidary.runtime.model.client_init.AuthModel').resolve())
