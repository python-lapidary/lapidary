import unittest
from collections.abc import AsyncIterator
from typing import Union

from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

from lapidary.runtime import ClientBase
from lapidary.runtime.model import ClientModel, ClientInit, OperationModel, ReturnTypeInfo


class TestIterator(unittest.IsolatedAsyncioTestCase):
    async def test_iterator(self):
        async def handler(_):
            return JSONResponse(['a', 'b', 'c'])

        app = Starlette(debug=True, routes=[
            Route('/strings', handler),
        ])

        model = ClientModel(
            init_method=ClientInit(
                response_map=None,
                base_url='http://example.com/',
                default_auth=None,
            ),
            methods=dict(
                get_strings=OperationModel(
                    'GET',
                    '/strings',
                    None,
                    {
                        '200': {
                            'application/json': ReturnTypeInfo(list[str], True)
                        }
                    },
                    None,
                )
            ),
        )

        client = ClientBase(_model=model, _app=app)
        response = await client.get_strings()
        self.assertIsInstance(response, AsyncIterator)
        self.assertEqual(['a', 'b', 'c'], [item async for item in response])

    async def test_iterator_union(self):
        async def handler(_):
            return JSONResponse(['a', 'b', 'c'])

        app = Starlette(debug=True, routes=[
            Route('/strings', handler),
        ])

        model = ClientModel(
            init_method=ClientInit(
                response_map=None,
                base_url='https://example.com/',
                default_auth=None,
            ),
            methods=dict(
                get_strings=OperationModel(
                    'GET',
                    '/strings',
                    None,
                    {
                        '200': {
                            'application/json': ReturnTypeInfo(Union[str, list[str]], True)
                        }
                    },
                    None,
                )
            ),
        )

        client = ClientBase(_model=model, _app=app)
        response = await client.get_strings()
        self.assertIsInstance(response, AsyncIterator)
        self.assertEqual(['a', 'b', 'c'], [item async for item in response])
