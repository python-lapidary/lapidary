import datetime as dt
from collections.abc import Awaitable
from unittest.mock import AsyncMock, Mock

import httpx
import pydantic
import pytest
import pytest_asyncio
import typing_extensions as typing

import lapidary.client
from lapidary import Body, Query, Responses, SimpleMultimap, UnexpectedResponse, get
from lapidary.http_consts import CONTENT_TYPE


class MyRequestBodyModel(pydantic.BaseModel):
    a: str


class MyRequestBodyList(pydantic.RootModel):
    root: list[MyRequestBodyModel]


@pytest_asyncio.fixture(scope='function')
async def mock_http_client():
    async with httpx.AsyncClient(base_url='http://example.com') as client:
        client.build_request = Mock(wraps=client.build_request)
        response = httpx.Response(543, request=httpx.Request('get', ''))

        client.send = AsyncMock(return_value=response)

        yield client


@pytest.mark.asyncio
async def test_build_request_from_list(mock_http_client) -> None:
    class Client:
        @get('/body_list')
        async def body_list(
            self: typing.Self,
            body: typing.Annotated[MyRequestBodyList, Body({'application/json': MyRequestBodyList})],
        ) -> typing.Annotated[Awaitable[None], Responses({})]:
            pass

    client = lapidary.client.for_api(Client, mock_http_client, '')
    with pytest.raises(UnexpectedResponse):
        await client.ops.body_list(body=MyRequestBodyList(root=[MyRequestBodyModel(a='a')]))

    mock_http_client.build_request.assert_called_with(
        'GET',
        '/body_list',
        content=b'[{"a":"a"}]',
        params=httpx.QueryParams(),
        headers=httpx.Headers(
            {
                CONTENT_TYPE: 'application/json',
            }
        ),
        cookies=httpx.Cookies(),
    )


@pytest.mark.asyncio
async def test_request_param_list_simple(mock_http_client):
    class Client:
        @get('/param_list_simple')
        async def param_list_simple(
            self: typing.Self,
            q_a: typing.Annotated[list[str], Query('a', style=SimpleMultimap)],
        ) -> typing.Annotated[Awaitable[None], Responses({})]:
            pass

    client = lapidary.client.for_api(Client, mock_http_client, '')
    with pytest.raises(UnexpectedResponse):
        await client.ops.param_list_simple(q_a=['hello', 'world'])

    mock_http_client.build_request.assert_called_with(
        'GET',
        '/param_list_simple',
        content=None,
        params=httpx.QueryParams(a='hello,world'),
        headers=httpx.Headers(),
        cookies=httpx.Cookies(),
    )


@pytest.mark.asyncio
async def test_build_request_none(mock_http_client):
    class Client:
        @get('/request_none')
        async def request_none(
            self: typing.Self,
        ) -> typing.Annotated[Awaitable[None], Responses({})]:
            pass

    client = lapidary.client.for_api(Client, mock_http_client, '')
    with pytest.raises(UnexpectedResponse):
        await client.ops.request_none()

    mock_http_client.build_request.assert_called_with(
        'GET',
        '/request_none',
        content=None,
        params=httpx.QueryParams(),
        headers=httpx.Headers(),
        cookies=httpx.Cookies(),
    )


@pytest.mark.asyncio
async def test_request_param_list_exploded(mock_http_client):
    class Client:
        @get('/param_list_exploded')
        async def param_list_exploded(
            self: typing.Self,
            q_a: typing.Annotated[list[str], Query('a', style=SimpleMultimap)],
        ) -> typing.Annotated[Awaitable[None], Responses({})]:
            pass

    client = lapidary.client.for_api(Client, mock_http_client, '')
    with pytest.raises(UnexpectedResponse):
        await client.ops.param_list_exploded(q_a=['hello', 'world'])

    mock_http_client.build_request.assert_called_with(
        'GET',
        '/param_list_exploded',
        content=None,
        params=httpx.QueryParams(a='hello,world'),
        headers=httpx.Headers(),
        cookies=httpx.Cookies(),
    )


@pytest.mark.asyncio
async def test_missing_required_param(mock_http_client):
    class Client:
        @get('/param_list_exploded')
        async def op(
            self: typing.Self,
            q_a: typing.Annotated[list[str], Query],
        ) -> typing.Annotated[Awaitable[None], Responses({})]:
            pass

    client = lapidary.client.for_api(Client, mock_http_client, '')
    with pytest.raises(TypeError):
        await client.ops.op()


@pytest.mark.asyncio
async def test_build_request_param_date(mock_http_client):
    class Client:
        @get('/request_date')
        async def request_date(
            self: typing.Self,
            date: typing.Annotated[dt.date, Query()],
        ) -> typing.Annotated[tuple[dt.date, None], Responses({})]:
            pass

    today = dt.date.today()

    client = lapidary.client.for_api(Client, mock_http_client, '')
    with pytest.raises(UnexpectedResponse):
        await client.ops.request_date(date=today)

    mock_http_client.build_request.assert_called_with(
        'GET',
        '/request_date',
        content=None,
        params=httpx.QueryParams({'date': today.isoformat()}),
        headers=httpx.Headers(),
        cookies=httpx.Cookies(),
    )
