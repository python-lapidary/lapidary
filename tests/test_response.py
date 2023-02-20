import unittest

from lapidary.runtime import openapi
from lapidary.runtime.http_consts import MIME_JSON
from lapidary.runtime.module_path import ModulePath
from lapidary.runtime.response import _status_code_matches

root = "lapidary_test"
root_module = ModulePath(root)

schema_carol = openapi.Schema()
schema_bob = openapi.Schema(properties={'carol': schema_carol})
model = openapi.OpenApiModel(
    openapi='3.0.3',
    info=openapi.Info(title='', version=''),
    paths=openapi.Paths(
        **{
            "/helo/": openapi.PathItem(
                get=openapi.Operation(
                    operationId="helo",
                    responses=openapi.Responses(
                        default=openapi.Response(
                            description="",
                            content={
                                MIME_JSON: openapi.MediaType(schema_=schema_bob)
                            }
                        ),
                        **{
                            "200": openapi.Reference(ref="#/components/responses/helo200Response"),
                            "4XX": openapi.Response(
                                description="",
                                content={
                                    MIME_JSON: openapi.MediaType(schema_=schema_bob)
                                }
                            )
                        }
                    ),
                )
            ),
        }
    ),
    components=openapi.Components(
        schemas={
            'bob': schema_bob,
        },
        responses={
            "helo200Response": openapi.Response(
                description="",
                content={
                    MIME_JSON: openapi.MediaType(schema_=schema_bob)
                }
            )
        }
    ),
    lapidary_responses_global=openapi.Responses(
        default=openapi.Response(
            description="",
            content={
                MIME_JSON: openapi.MediaType(schema_=schema_bob)
            }
        ),
        **{"200": openapi.Reference(ref="#/components/responses/helo200Response")}
    ),
)


class MatchResponseCodeTest(unittest.TestCase):
    def test__status_code_matches(self):
        matches = list(_status_code_matches('400'))
        self.assertEqual(['400', '4XX', 'default'], matches)


class ResponseMapTest(unittest.TestCase):
    def test_response_type_hint(self):
        pass
