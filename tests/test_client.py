import datetime as dt
import email.utils

import fastapi
import httpx
import pydantic
import pytest
import typing_extensions as typing
from fastapi.responses import JSONResponse

from lapidary.runtime import (
    Body,
    ClientBase,
    Header,
    HttpErrorResponse,
    Metadata,
    ModelBase,
    Path,
    Response,
    Responses,
    SimpleString,
    StatusCode,
    UnexpectedResponse,
    get,
    post,
)
from lapidary.runtime.http_consts import MIME_JSON

# model (common to both client and server)


class Cat(pydantic.BaseModel):
    id: typing.Optional[int] = None
    name: str


class AuthRequest(pydantic.BaseModel):
    login: str
    password: str


class AuthResponse(pydantic.BaseModel):
    api_key: str


class ServerErrorModel(ModelBase):
    msg: str


DATE = dt.datetime(2024, 7, 28, 0, 55, tzinfo=dt.timezone.utc)

# FastAPI server

cats_app = fastapi.FastAPI(debug=True)


@cats_app.get('/cats', responses={'200': {'model': typing.List[Cat]}})
async def cat_list(
    return_list: typing.Annotated[typing.Optional[bool], fastapi.Header()] = None,
    token: typing.Annotated[typing.Optional[str], fastapi.Header()] = None,
) -> JSONResponse:
    assert isinstance(return_list, (bool, type(None)))
    serializer = pydantic.TypeAdapter(typing.List[Cat])
    data = [Cat(id=1, name='Tom')]
    headers = {
        'X-Count': str(len(data)),
        'Date': DATE.strftime('%a, %d %b %Y %H:%M:%S %Z'),
        'returning_list': 'true' if return_list else 'false',
    }
    if token:
        headers['token'] = token
    return JSONResponse(
        serializer.dump_python(data),
        headers=headers,
    )


@cats_app.get(
    '/cat/{cat_id}',
    responses={
        '2XX': {MIME_JSON: Cat},
        '4XX': {MIME_JSON: ServerErrorModel},
    },
)
async def get_cat(cat_id: int) -> JSONResponse:
    if cat_id != 1:
        return JSONResponse(pydantic.TypeAdapter(ServerErrorModel).dump_python(ServerErrorModel(msg='Cat not found')), 404)
    return JSONResponse(Cat(id=1, name='Tom').model_dump(), 200)


class CatWriteDTO(pydantic.BaseModel):
    name: str
    model_config = pydantic.ConfigDict(extra='forbid')


@cats_app.post('/cat/')
async def create_cat(cat: CatWriteDTO) -> JSONResponse:
    print(cat.model_dump())
    return JSONResponse(Cat(name=cat.name, id=2).model_dump(), 201)


@cats_app.post('/login')
async def login(body: AuthRequest) -> AuthResponse:
    assert body.login == 'login'
    assert body.password == 'passwd'

    return AuthResponse(api_key="you're in")


# Client


class CatListRequestHeaders(pydantic.BaseModel):
    token: typing.Annotated[typing.Optional[str], Header] = None
    return_list: typing.Annotated[typing.Optional[bool], Header('return-list')] = None


class CatListResponseHeaders(pydantic.BaseModel):
    count: typing.Annotated[int, Header('X-Count')]
    token: typing.Annotated[typing.Optional[str], Header] = None
    date: typing.Annotated[
        dt.datetime,
        Header,
        pydantic.BeforeValidator(email.utils.parsedate_to_datetime),
    ]
    status_code: typing.Annotated[int, StatusCode]
    returning_list: typing.Annotated[bool, Header]


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
        meta: typing.Annotated[CatListRequestHeaders, Metadata],
    ) -> typing.Annotated[
        tuple[list[Cat], CatListResponseHeaders],
        Responses(
            {
                'default': Response(Body({'application/json': list[Cat]}), CatListResponseHeaders),
            }
        ),
    ]:
        pass

    @get('/cat/{id}')
    async def cat_get(
        self: typing.Self,
        *,
        id: typing.Annotated[int, Path(style=SimpleString)],  # pylint: disable=redefined-builtin
    ) -> typing.Annotated[
        tuple[Cat, None],
        Responses(
            {
                '2XX': Response(Body({'application/json': Cat})),
                '4XX': Response(Body({'application/json': ServerErrorModel})),
            }
        ),
    ]:
        pass

    @post('/cat/')
    async def cat_create(
        self: typing.Self,
        *,
        body: typing.Annotated[Cat, Body({'application/json': Cat})],
    ) -> typing.Annotated[
        tuple[Cat, None],
        Responses(
            {
                '2XX': Response(Body({'application/json': Cat})),
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
        tuple[AuthResponse, None],
        Responses(
            {
                '200': Response(
                    Body(
                        {
                            MIME_JSON: AuthResponse,
                        }
                    )
                )
            }
        ),
    ]:
        pass


# tests

client = CatClient(transport=httpx.ASGITransport(app=cats_app))


@pytest.mark.asyncio
async def test_request_response():
    response_body, response_headers = await client.cat_list(
        meta=CatListRequestHeaders(
            token='header-value',
            return_list=True,
        )
    )
    assert response_headers.status_code == 200
    assert response_headers.count == 1
    assert response_headers.token == 'header-value'
    assert response_headers.date == DATE
    assert response_headers.returning_list is True
    assert response_body == [Cat(id=1, name='Tom')]

    response_body, response_headers = await client.cat_list()
    assert response_headers.token is None

    cat, _ = await client.cat_get(id=1)
    assert isinstance(cat, Cat)
    assert cat == Cat(id=1, name='Tom')


@pytest.mark.asyncio
async def test_response_auth():
    response, _ = await client.login(body=AuthRequest(login='login', password='passwd'))

    assert response.api_key == "you're in"


@pytest.mark.asyncio
async def test_error():
    try:
        await client.cat_get(id=7)
        assert False, 'Expected ServerError'
    except HttpErrorResponse as e:
        assert isinstance(e.body, ServerErrorModel)
        assert e.body.msg == 'Cat not found'


@pytest.mark.asyncio
async def test_create():
    body, _ = await client.cat_create(body=Cat(name='Benny'))
    assert body.id == 2
    assert body.name == 'Benny'


@pytest.mark.asyncio
async def test_create_error():
    with pytest.raises(UnexpectedResponse) as error:
        await client.cat_create(body=Cat(id=1, name='Benny'))
    assert error.value.response.status_code == 422
