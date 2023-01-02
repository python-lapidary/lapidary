import typing
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
    paths=openapi.Paths(),
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
        from lapidary.runtime.model.auth import AuthModel
        self.assertEqual(AuthModel, TypeHint.from_str('lapidary.runtime.model.auth.AuthModel').resolve())


def test_from_type_union():
    assert TypeHint.from_type(typing.Union) == TypeHint(module='typing', name='Union')


def test_origin():
    type_ = GenericTypeHint(module='typing', name='Union', args=(TypeHint.from_type(str), TypeHint.from_type(int)))
    assert TypeHint.from_type(typing.Union) == type_.origin
