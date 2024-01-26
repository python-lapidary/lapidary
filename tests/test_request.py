from unittest.mock import AsyncMock, Mock

import httpx
import pydantic
import pytest
import pytest_asyncio
import typing_extensions as typing

from lapidary.runtime import Query, RequestBody, Responses, get
from lapidary.runtime.http_consts import CONTENT_TYPE
from lapidary.runtime.model.params import ParamStyle
from tests.client import ClientTestBase


class MyRequestBodyModel(pydantic.BaseModel):
    a: str


class MyRequestBodyList(pydantic.RootModel):
    root: typing.List[MyRequestBodyModel]


@pytest_asyncio.fixture(scope='function')
async def mock_http_client():
    client = httpx.AsyncClient(base_url='http://example.com')
    client.build_request = Mock(wraps=client.build_request)
    response = httpx.Response(543, request=httpx.Request('get', ''))

    client.send = AsyncMock(return_value=response)

    yield client


@pytest.mark.asyncio
async def test_build_request_from_list(mock_http_client) -> None:
    class Client(ClientTestBase):
        @get('/body_list')
        async def body_list(
                self: typing.Self,
                body: typing.Annotated[MyRequestBodyList, RequestBody({'application/json': MyRequestBodyList})]
        ) -> typing.Annotated[None, Responses({})]:
            pass

    async with Client(client=mock_http_client) as client:
        await client.body_list(body=MyRequestBodyList(root=[MyRequestBodyModel(a='a')]))

    mock_http_client.build_request.assert_called_with(
        'GET',
        '/body_list',
        content='[{"a":"a"}]',
        params=httpx.QueryParams(),
        headers=httpx.Headers({
            CONTENT_TYPE: 'application/json',
        }),
        cookies=httpx.Cookies(),
    )


@pytest.mark.asyncio
async def test_request_param_list_simple(mock_http_client):
    class Client(ClientTestBase):
        @get('/param_list_simple')
        async def param_list_simple(
                self: typing.Self,
                q_a: typing.Annotated[typing.List[str], Query('a', style=ParamStyle.simple)]
        ) -> typing.Annotated[None, Responses({})]:
            pass

    async with Client(client=mock_http_client) as client:
        await client.param_list_simple(q_a=['hello', 'world'])

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
    class Client(ClientTestBase):
        @get('/request_none')
        async def request_none(
                self: typing.Self,
        ) -> typing.Annotated[None, Responses({})]:
            pass

    async with Client(client=mock_http_client) as client:
        await client.request_none()

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
    class Client(ClientTestBase):
        @get('/param_list_exploded')
        async def param_list_exploded(
                self: typing.Self,
                q_a: typing.Annotated[typing.List[str], Query('a', style=ParamStyle.simple, explode=True)]
        ) -> typing.Annotated[None, Responses({})]:
            pass

    async with Client(client=mock_http_client) as client:
        await client.param_list_exploded(q_a=['hello', 'world'])

    mock_http_client.build_request.assert_called_with(
        'GET',
        '/param_list_exploded',
        content=None,
        params=httpx.QueryParams([('a', 'hello'), ('a', 'world')]),
        headers=httpx.Headers(),
        cookies=httpx.Cookies(),
    )
