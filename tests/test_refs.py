from unittest import TestCase

from lapidary.runtime import openapi
from lapidary.runtime.http_consts import MIME_JSON
from lapidary.runtime.model.refs import resolve
from lapidary.runtime.model.type_hint import TypeHint
from lapidary.runtime.model import get_type_hint
from lapidary.runtime.module_path import ModulePath

root = "lapidary_test"
root_module = ModulePath(root)

schema_carol = openapi.Schema()
schema_bob = openapi.Schema(properties={'carol': schema_carol})
operation = openapi.Operation(
    operationId="helo",
    responses=openapi.Responses(
        default=openapi.Response(
            description="",
            content={
                MIME_JSON: openapi.MediaType(schema_=schema_bob)
            }
        )

    ),
)
model = openapi.OpenApiModel(
    openapi='3.0.3',
    info=openapi.Info(title='', version=''),
    paths=openapi.Paths(
        **{
            "/helo/": openapi.PathItem(
                get=operation,
            ),
        }
    ),
    components=openapi.Components(
        schemas={
            'alice': openapi.Reference(ref='#/components/schemas/bob'),
            'bob': schema_bob,

            'joker': openapi.Reference(ref='#/components/schemas/joker'),

            'batman': openapi.Reference(ref='#/components/schemas/robin'),
            'robin': openapi.Reference(ref='#/components/schemas/batman'),

            'charlie': openapi.Schema(oneOf=[
                openapi.Schema()
            ]),
        }
    )
)


class ReferenceTest(TestCase):
    def test_resolve_ref(self):
        resolved = resolve(model, 'root', openapi.Reference(ref='#/components/schemas/alice'), openapi.Schema)
        self.assertEqual(
            (schema_bob, ModulePath('root.components.schemas.bob'), 'bob'),
            resolved,
        )

    def test_nested_schema(self):
        self.assertEqual(
            (schema_carol, ModulePath('root.components.schemas.bob.properties.carol'), 'carol'),
            resolve(model, 'root', openapi.Reference(ref='#/components/schemas/bob/properties/carol'), openapi.Schema),
        )

    def test_direct_recursion_fails(self):
        with self.assertRaises(RecursionError):
            resolve(model, 'root', openapi.Reference(ref='#/components/schemas/joker'), openapi.Schema)

    def test_indirect_recursion_fails(self):
        def raises():
            resolve(model, 'root', openapi.Reference(ref='#/components/schemas/batman'), openapi.Schema)

        self.assertRaises(RecursionError, raises)

    def test_empty_schema_generate_any_type_ref(self):
        type_ref = get_type_hint(openapi.Schema(), root_module, root, True, None)
        self.assertEqual(type_ref, TypeHint.from_str('typing:Any'))


def test_resolve_operation():
    op, path, name = resolve(model, root, openapi.Reference(ref="#/paths/~1helo~1/get"), openapi.Operation)
    assert op == operation
    assert path == ModulePath("lapidary_test.ops.helo")
    assert name == "get"


def test_resolve_schema():
    schema, path, name = resolve(model, root, openapi.Reference(ref="#/paths/~1helo~1/get/responses/default/content/application~1json/schema"), openapi.Schema)
    assert schema == schema_bob
    assert path == ModulePath("lapidary_test.ops.helo.responses.default.content.applicationu_00002fjson")
    assert name == "schema"
