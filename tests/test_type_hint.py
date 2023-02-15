import typing
from unittest import TestCase

from lapidary.runtime import openapi
from lapidary.runtime.model import get_type_hint
from lapidary.runtime.model.refs import get_resolver
from lapidary.runtime.model.type_hint import GenericTypeHint, TypeHint, from_type
from lapidary.runtime.module_path import ModulePath

schema_carol = openapi.Schema()
schema_bob = openapi.Schema(properties={'carol': schema_carol})
model = openapi.OpenApiModel(
    openapi='3.0.3',
    info=openapi.Info(title='', version=''),
    paths=openapi.Paths(**{
        "/a": openapi.PathItem(
            post=openapi.Operation(
                operationId="op_a",
                parameters=[
                    openapi.Parameter(
                        name="param_a",
                        in_=openapi.In1.query.value,
                        schema=openapi.Schema(
                            type=openapi.Type.string,
                        )
                    ),
                ],
                responses=openapi.Responses(
                    **{"default": openapi.Response(
                        description="",
                    )}
                ),
            )
        )
    }),
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
            GenericTypeHint(module='typing', type_name='Union', args=(
                from_type(str),
                from_type(int),
            )),
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
            GenericTypeHint(module='typing', type_name='Union', args=(
                from_type(str),
                from_type(int),
            )),
            get_type_hint(
                model.components.schemas['bob'],
                ModulePath('mymodule'),
                'Bob',
                True,
                get_resolver(model, 'mypackage')
            )
        )


def test_from_type_union():
    assert from_type(typing.Union) == TypeHint(module='typing', type_name='Union')


def test_origin():
    type_ = GenericTypeHint(module='typing', type_name='Union', args=(
        from_type(str),
        from_type(int)
    ))
    assert from_type(typing.Union) == type_.origin
