import dataclasses as dc

import fastapi
import httpx
import pydantic
import pytest
import typing_extensions as typing
from starlette.responses import JSONResponse

from lapidary.runtime import Body, ClientBase, Header, ParamStyle, Path, Responses, get, post, put
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


@cats_app.get('/cats', responses={'200': {'model': typing.List[Cat]}})
async def cat_list() -> JSONResponse:
    serializer = pydantic.TypeAdapter(typing.List[Cat])
    data = [Cat(id=1, name='Tom')]
    return JSONResponse(
        serializer.dump_python(data),
        headers={'X-Count': str(len(data))},
    )


@cats_app.get(
    '/cat/{cat_id}',
    responses={
        '2XX': {MIME_JSON: Cat},
        '4XX': {MIME_JSON: ServerError},
    },
)
async def get_cat(cat_id: int) -> JSONResponse:
    if cat_id != 1:
        return JSONResponse(pydantic.TypeAdapter(ServerError).dump_python(ServerError('Cat not found')), 404)
    return JSONResponse(Cat(id=1, name='Tom').model_dump(), 200)


@cats_app.post('/login')
async def login(body: AuthRequest) -> AuthResponse:
    assert body.login == 'login'
    assert body.password == 'passwd'

    return AuthResponse(api_key="you're in")


# Client


class CatListHeaders(pydantic.BaseModel):
    count: typing.Annotated[int, Header('X-Count')]


class CatClient(ClientBase):
    def __init__(
        self,
        base_url='http://localhost',
        **httpx_args,
    ):
        super().__init__(
            base_url=base_url,
            **httpx_args,
        )

    @get('/cats')
    async def cat_list(
        self: typing.Self,
    ) -> typing.Annotated[
        tuple[list[Cat], CatListHeaders],
        Responses(
            {
                'default': {'application/json': list[Cat]},
            }
        ),
    ]:
        pass

    @get('/cat/{id}')
    async def cat_get(
        self: typing.Self,
        *,
        id: typing.Annotated[int, Path(style=ParamStyle.simple)],  # pylint: disable=redefined-builtin
    ) -> typing.Annotated[
        Cat,
        Responses(
            {
                '2XX': {'application/json': Cat},
                '4XX': {'application/json': ServerError},
            }
        ),
    ]:
        pass

    @put('/cat')
    async def cat_update(
        self: typing.Self,
        *,
        body: typing.Annotated[Cat, Body({'application/json': Cat})],
    ) -> typing.Annotated[
        Cat,
        Responses(
            {
                'default': {'application/json': Cat},
            }
        ),
    ]:
        pass

    @post('/login')
    async def login(
        self: typing.Self,
        *,
        body: typing.Annotated[AuthRequest, Body({MIME_JSON: AuthRequest})],
    ) -> typing.Annotated[
        AuthResponse,
        Responses(
            {
                '200': {
                    MIME_JSON: AuthResponse,
                }
            }
        ),
    ]:
        pass


# tests

client = CatClient(transport=httpx.ASGITransport(app=cats_app))


@pytest.mark.asyncio
async def test_request_response():
    response_body, response_headers = await client.cat_list()
    assert isinstance(response_body, list)
    assert response_body == [Cat(id=1, name='Tom')]
    assert response_headers.count == 1

    cat = await client.cat_get(id=1)
    assert isinstance(cat, Cat)
    assert cat == Cat(id=1, name='Tom')


@pytest.mark.asyncio
async def test_response_auth():
    response = await client.login(body=AuthRequest(login='login', password='passwd'))

    assert response.api_key == "you're in"


@pytest.mark.asyncio
@pytest.mark.skip(reason='raising errors not implemented')
async def test_error():
    try:
        await client.cat_get(id=7)
        assert False, 'Expected ServerError'
    except ServerError as e:
        assert e.msg == 'Cat not found'
