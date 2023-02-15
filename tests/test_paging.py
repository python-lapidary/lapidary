import unittest
from collections.abc import AsyncIterator
from typing import Generator, List

import httpx
import starlette.requests
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

from lapidary.runtime import ClientBase
from lapidary.runtime.http_consts import MIME_JSON
from lapidary.runtime.model import ClientModel, OperationModel, PagingPlugin
from lapidary.runtime.model.response_map import ReturnTypeInfo


class XTestPagingPlugin(PagingPlugin):
    def page_flow(self, request: httpx.Request) -> Generator[httpx.Request, httpx.Response, None]:
        while True:
            response: httpx.Response = yield request
            next_url = response.links.get('next')
            if not next_url:
                return
            request = httpx.Request(request.method, next_url['url'], headers=request.headers)


async def handler(request: starlette.requests.Request) -> starlette.responses.Response:
    headers = {}
    if not request.query_params:
        headers['Link'] = '<https://example.com/strings?page=next>; rel="next'

    return JSONResponse(['a', 'b', 'c'], headers=headers)


class TestIterator(unittest.IsolatedAsyncioTestCase):
    async def test_paging(self):
        app = Starlette(debug=True, routes=[
            Route('/strings', handler),
        ])

        model = ClientModel(
            response_map={},
            base_url='https://example.com/',
            default_auth=None,
            methods=dict(
                get_strings=OperationModel(
                    'GET',
                    '/strings',
                    [],
                    {
                        '200': {
                            MIME_JSON: ReturnTypeInfo(List[str], False)
                        }
                    },
                    XTestPagingPlugin(),
                ),
            ),
        )

        client = ClientBase(_model=model, _app=app)
        response = await client.get_strings()
        self.assertIsInstance(response, AsyncIterator)
        self.assertEqual([['a', 'b', 'c'], ['a', 'b', 'c']], [item async for item in response])

    async def test_iterator(self):
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
                            MIME_JSON: ReturnTypeInfo(List[str], True)
                        }
                    },
                    XTestPagingPlugin(),
                ),
            ),
        )

        client = ClientBase(_model=model, _app=app)
        response = await client.get_strings()
        self.assertIsInstance(response, AsyncIterator)
        self.assertEqual(['a', 'b', 'c', 'a', 'b', 'c'], [item async for item in response])