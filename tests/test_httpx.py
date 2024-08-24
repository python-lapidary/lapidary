"""Never test third-party code..."""

import httpx
import pytest
import pytest_asyncio
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route


@pytest_asyncio.fixture
async def client_server() -> httpx.AsyncClient:
    async def request(request: Request):
        return JSONResponse(
            {
                'url': str(request.url),
                'param': request.query_params.getlist('param'),
                'header': request.headers.getlist('param'),
                'cookie': request.cookies.get('param'),
            }
        )

    app = Starlette(
        debug=True,
        routes=[
            Route('/', request),
        ],
    )

    async with httpx.AsyncClient(base_url='http://example.com', transport=httpx.ASGITransport(app)) as client:
        yield client


@pytest.mark.asyncio
async def test_query_array_serialization(client_server: httpx.AsyncClient):
    response = await client_server.get('http://example.com', params=httpx.QueryParams({'param': ('value1', 'value2')}))
    json = response.json()
    assert json['param'] == ['value1', 'value2']
    assert json['url'] == 'http://example.com/?param=value1&param=value2'


@pytest.mark.asyncio
async def test_query_array_as_tuple_list_serialization(client_server: httpx.AsyncClient):
    response = await client_server.get('http://example.com', params=httpx.QueryParams([('param', 'value1'), ('param', 'value2')]))
    json = response.json()
    assert json['param'] == ['value1', 'value2']
    assert json['url'] == 'http://example.com/?param=value1&param=value2'


@pytest.mark.asyncio
async def test_header_array_explode_serialization(client_server: httpx.AsyncClient):
    response = await client_server.get(
        'http://example.com',
        headers=httpx.Headers(
            [
                ('param', 'value1'),
                ('param', 'value2'),
            ]
        ),
    )
    assert response.json().get('header') == ['value1', 'value2']


@pytest.mark.asyncio
async def test_header_array_serialization(client_server: httpx.AsyncClient):
    """Both httpx and starlette seem to ignore the comma in value"""
    response = await client_server.get(
        'http://example.com',
        headers=httpx.Headers(
            {
                'param': 'value1,value2',
            }
        ),
    )
    assert response.json().get('header') == ['value1,value2']


@pytest.mark.asyncio
async def test_cookie_array_explode_serialization(client_server: httpx.AsyncClient):
    """Both httpx and starlette seem to ignore the comma in value"""
    response = await client_server.get(
        'http://example.com',
        cookies=httpx.Cookies(
            [
                ('param', 'value1'),
                ('param', 'value2'),
            ]
        ),
    )
    assert response.json().get('cookie') == 'value2'
