import unittest
from typing import List

from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

from lapidary.runtime import ClientBase
from lapidary.runtime.model import ClientModel, OperationModel, ReturnTypeInfo


class TestClient(unittest.IsolatedAsyncioTestCase):
    async def test_request(self):
        async def handler(_):
            return JSONResponse(['a', 'b', 'c'])

        app = Starlette(debug=True, routes=[
            Route('/strings', handler),
        ])

        model = ClientModel(
            response_map={},
            base_url='http://example.com/',
            default_auth=None,
            methods=dict(
                get_strings=OperationModel(
                    'GET',
                    '/strings',
                    [],
                    {
                        '200': {
                            'application/json': ReturnTypeInfo(List[str], False)
                        }
                    },
                    None,
                )
            ),
        )

        client = ClientBase(_model=model, _app=app)
        response = await client.get_strings()
        self.assertIsInstance(response, list)
        self.assertEqual(['a', 'b', 'c'], response)
