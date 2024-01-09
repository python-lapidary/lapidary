import inspect
import logging
import unittest

import httpx
import pydantic
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

from lapidary.runtime import APIKeyAuth, ClientBase, GET, POST
from lapidary.runtime.compat import typing as ty
from lapidary.runtime.model.op import get_response_map
from lapidary.runtime.model.response_map import Responses

logger = logging.getLogger(__name__)
logging.getLogger('lapidary').setLevel(logging.DEBUG)


class AuthResponse(pydantic.BaseModel):
    api_key: str


class Client(ClientBase):
    @GET('/strings')
    async def get_strings(self: ty.Self) -> ty.Annotated[
        ty.List[str],
        Responses({
            '200': {
                'application/json': ty.List[str]
            }
        })
    ]:
        pass

    @POST('/login')
    async def login(self: ty.Self,
                    ) -> ty.Annotated[
        httpx.Auth,
        Responses({
            '200': {
                'application/json': ty.Annotated[
                    AuthResponse,
                    APIKeyAuth(
                        'header',
                        'Authorization',
                        'Token {body.api_key}'
                    ),
                ]
            }
        })
    ]:
        pass


class TestClient(unittest.IsolatedAsyncioTestCase):
    async def test_request(self):
        async def handler(_):
            return JSONResponse(['a', 'b', 'c'])

        app = Starlette(debug=True, routes=[
            Route('/strings', handler),
        ])

        client = Client(base_url='http://example.com', app=app)
        response = await client.get_strings()
        self.assertIsInstance(response, list)
        self.assertEqual(['a', 'b', 'c'], response)

    async def test_response_auth(self):
        async def handler(_):
            return JSONResponse({'api_key': 'token'})

        app = Starlette(debug=True, routes=[
            Route('/login', handler, methods=['POST']),
        ])

        client = Client(base_url='http://example.com', app=app)
        response = await client.login()
        self.assertEqual(dict(api_key='Token token', header_name='Authorization'), response.__dict__)


class TestClientSync(unittest.TestCase):
    def test_missing_return_anno(self):
        async def operation():
            pass

        sig = inspect.signature(operation)
        with self.assertRaises(TypeError):
            get_response_map(sig.return_annotation)
