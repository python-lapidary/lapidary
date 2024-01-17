# mypy: disable-error-code="empty-body"

import dataclasses as dc
import unittest

import fastapi
import httpx
import httpx_auth
import pydantic
from starlette.responses import JSONResponse

from lapidary.runtime import APIKeyAuth, ClientBase, get, post, put, ParamStyle, Path, RequestBody, Responses
from lapidary.runtime.compat import typing as ty
from lapidary.runtime.http_consts import MIME_JSON


# model (common to both client and server)

class Cat(pydantic.BaseModel):
    id: int
    name: str


class AuthRequest(pydantic.BaseModel):
    login: str
    password: str


class AuthResponse(pydantic.BaseModel):
    api_key: str


@dc.dataclass
class ServerError(Exception):
    msg: str


# FastAPI server

cats_app = fastapi.FastAPI(debug=True)


@cats_app.get('/cats')
async def cat_list() -> ty.List[Cat]:
    return [Cat(id=1, name="Tom")]


@cats_app.get('/cat/{cat_id}', responses={
    '2XX': {
        MIME_JSON: Cat
    },
    '4XX': {
        MIME_JSON: ServerError
    }
})
async def get_cat(cat_id: int) -> JSONResponse:
    if cat_id != 1:
        return JSONResponse(pydantic.TypeAdapter(ServerError).dump_python(ServerError('Cat not found')), 404)
    return JSONResponse(Cat(id=1, name="Tom").model_dump(), 200)


@cats_app.post('/login')
async def login(body: AuthRequest) -> AuthResponse:
    assert body.login == 'login'
    assert body.password == 'passwd'

    return AuthResponse(api_key="you're in")


# Client


class CatClient(ClientBase):
    def __init__(self, **httpx_args):
        super().__init__(
            base_url='http://localhost',
            **httpx_args,
            follow_redirects=False,
        )

    @get('/cats')
    async def cat_list(
            self: ty.Self,
    ) -> ty.Annotated[Cat, Responses({
        'default': {
            'application/json': ty.List[Cat]
        },
    })]:
        pass

    @get('/cat/{id}')
    async def cat_get(
            self: ty.Self,
            *,
            id: ty.Annotated[int, Path(style=ParamStyle.simple)],  # pylint: disable=redefined-builtin
    ) -> ty.Annotated[Cat, Responses({
        '2XX': {
            'application/json': Cat
        },
        '4XX': {
            'application/json': ServerError
        },
    })]:
        pass

    @put('/cat')
    async def cat_update(
            self: ty.Self,
            *,
            body: ty.Annotated[Cat, RequestBody({'application/json': Cat})],
    ) -> ty.Annotated[Cat, Responses({
        'default': {
            'application/json': Cat
        }
    })]:
        pass

    @post('/login')
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


# tests

client = CatClient(app=cats_app)


class TestClient(unittest.IsolatedAsyncioTestCase):
    async def test_request(self):
        response = await client.cat_list()
        self.assertIsInstance(response, list)
        self.assertEqual([Cat(id=1, name='Tom')], response)

        cat = await client.cat_get(id=1)
        self.assertIsInstance(cat, Cat)
        self.assertEqual(Cat(id=1, name='Tom'), cat)

    async def test_response_auth(self):
        response = await client.login(body=AuthRequest(login='login', password='passwd'))
        self.assertDictEqual(
            httpx_auth.HeaderApiKey("Token you're in", 'Authorization').__dict__,
            response.__dict__
        )

    async def test_error(self):
        try:
            await client.cat_get(id=7)
            assert False, 'Expected ServerError'
        except ServerError as e:
            self.assertEqual(e.msg, "Cat not found")
