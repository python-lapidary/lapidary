import unittest
from collections.abc import Iterator, AsyncIterator
from typing import Generator

import httpx
import starlette.requests
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

from lapidary.runtime import ClientBase
from lapidary.runtime.model import ClientModel, ClientInit, OperationModel, PagingPlugin


class TestPagingPlugin(PagingPlugin):
    def page_flow(self, request: httpx.Request) -> Generator[httpx.Request, httpx.Response, None]:
        while True:
            response: httpx.Response = yield request
            next_url = response.links.get('next')
            if not next_url:
                return
            request = httpx.Request(request.method, next_url['url'], headers=request.headers)


class TestIterator(unittest.IsolatedAsyncioTestCase):
    async def test_paging(self):
        async def handler(request: starlette.requests.Request) -> starlette.responses.Response:
            print(request)
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
                            'application/json': list[str]
                        }
                    },
                    TestPagingPlugin(),
                ),
            ),
        )

        client = ClientBase(_model=model, _app=app)
        response = await client.get_strings()
        self.assertIsInstance(response, AsyncIterator)
        self.assertEqual(['a', 'b', 'c'], [item async for item in response])

    async def test_iterator(self):
        async def handler(request: starlette.requests.Request) -> starlette.responses.Response:
            print(request)
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
                            'application/json': Iterator[str]
                        }
                    },
                    TestPagingPlugin(),
                ),
            ),
        )

        client = ClientBase(_model=model, _app=app)
        response = await client.get_strings()
        self.assertIsInstance(response, AsyncIterator)
        self.assertEqual(['a', 'b', 'c'], [item async for item in response])
