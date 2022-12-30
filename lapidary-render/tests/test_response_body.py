from unittest import TestCase

from lapidary.runtime import openapi
from lapidary.runtime.module_path import ModulePath

from lapidary.render.model.response_body import get_response_body_classes


class TestResponseBody(TestCase):
    def test_get_response_body_classes(self):
        op = openapi.Operation(
            operationId='op',
            responses=openapi.Responses(**dict(
                default=openapi.Response(
                    description='',
                    content={
                        'image/png': dict(),
                    }
                )
            ))
        )
        self.assertEqual(
            [],
            list(get_response_body_classes(op, ModulePath('test'), None))
        )
