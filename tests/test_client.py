import logging
import unittest

from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

from lapidary.runtime import ClientBase, GET
from lapidary.runtime.model import ReturnTypeInfo
from lapidary.runtime.compat import typing as ty
from lapidary.runtime.model.response_map import Responses

import logging

logger = logging.getLogger(__name__)
logging.getLogger('lapidary').setLevel(logging.DEBUG)


class Client(ClientBase):
    @GET('/strings')
    async def get_strings(self: typing_extensions.Self) -> typing.Annotated[
        List[str], Responses({
    async def get_strings(self: ty.Self) -> ty.Annotated[
        ty.List[str],
        Responses({
            '200': {
                'application/json': ty.List[str]
            }
        })
    ]:
        ...


class TestClient(unittest.IsolatedAsyncioTestCase):
    async def test_request(self):
        async def handler(_):
            return JSONResponse(['a', 'b', 'c'])

        app = Starlette(debug=True, routes=[
            Route('/strings', handler),
        ])

        client = Client('http://example.com', _app=app)
        response = await client.get_strings()
        self.assertIsInstance(response, list)
        self.assertEqual(['a', 'b', 'c'], response)
