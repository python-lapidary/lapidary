import dataclasses as dc
import http
import inspect
import unittest

import fastapi
import httpx
import pydantic

from lapidary.runtime import APIKeyAuth, ClientBase, GET, Header, POST, RequestBody, Responses
from lapidary.runtime.compat import typing as ty
from lapidary.runtime.http_consts import MIME_JSON
from lapidary.runtime.model.op import get_response_map


# model (common to both client and server)

class AuthRequest(pydantic.BaseModel):
    login: str
    password: str


class AuthResponse(pydantic.BaseModel):
    api_key: str


@dc.dataclass
class ServerError(Exception):
    msg: str


# FastAPI server

app = fastapi.FastAPI(debug=True)


@app.get('/strings')
async def get_strings() -> list[str]:
    return ['a', 'b', 'c']


@app.post('/login')
async def login(body: AuthRequest) -> AuthResponse:
    assert body.login == 'login'
    assert body.password == 'passwd'

    return AuthResponse(api_key='token')


@app.get('/err', status_code=http.HTTPStatus.IM_A_TEAPOT)
async def err() -> ServerError:
    return ServerError("I'm actually a samovar")


# Client

class Client(ClientBase):
    @GET('/strings')
    async def get_strings(
            self: ty.Self,
            accept: ty.Annotated[str, Header()] = MIME_JSON,
    ) -> ty.Annotated[
        ty.List[str],
        Responses({
            '200': {
                MIME_JSON: ty.List[str]
            }
        })
    ]:
        pass

    @POST('/login')
    async def login(
            self: ty.Self,
            *,
            body: ty.Annotated[AuthRequest, RequestBody({MIME_JSON: AuthRequest})],
    ) -> ty.Annotated[
        httpx.Auth,
        Responses({
            '200': {
                MIME_JSON: ty.Annotated[
                    AuthResponse,
                    APIKeyAuth(
                        'header',
                        'Authorization',
                        'Token {body.api_key}'
                    ),
                ]
            }
        }),
    ]:
        pass

    @GET('/err')
    async def err(self: ty.Self) -> ty.Annotated[ServerError, Responses({
        str(http.HTTPStatus.IM_A_TEAPOT): {MIME_JSON: ServerError}
    })]:
        pass


client = Client(base_url='http://example.com', app=app)


# tests

class TestClient(unittest.IsolatedAsyncioTestCase):
    async def test_request(self):
        response = await client.get_strings()
        self.assertIsInstance(response, list)
        self.assertEqual(['a', 'b', 'c'], response)

    async def test_response_auth(self):
        response = await client.login(body=AuthRequest(login='login', password='passwd'))
        self.assertEqual(dict(api_key='Token token', header_name='Authorization'), response.__dict__)

    async def test_error(self):
        try:
            await client.err()
            assert False, 'Expected ServerError'
        except ServerError as e:
            self.assertEqual(e.msg, "I'm actually a samovar")


class TestClientSync(unittest.TestCase):
    def test_missing_return_anno(self):
        async def operation():
            pass

        sig = inspect.signature(operation)
        with self.assertRaises(TypeError):
            get_response_map(sig.return_annotation)
