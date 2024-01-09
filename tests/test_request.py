from typing import List
import unittest
from unittest.mock import Mock

import httpx
from httpx import Cookies, Headers, QueryParams
import pydantic

from lapidary.runtime import ParamLocation
from lapidary.runtime.model.op import OperationModel
from lapidary.runtime.model.params import FullParam, ParamStyle
from lapidary.runtime.model.request import RequestBodyModel
from lapidary.runtime.request import build_request


class BuildRequestAsyncTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_build_request_from_list(self) -> None:
        class MyRequestBodyModel(pydantic.BaseModel):
            a: str

        class MyRequestBodyList(pydantic.RootModel):
            root: List[MyRequestBodyModel]

        request_factory = Mock()
        build_request(
            operation=OperationModel('GET', 'path', {}, RequestBodyModel('body', {'application/json': MyRequestBodyList}), {}),
            actual_params={'body': MyRequestBodyList([MyRequestBodyModel(a='a')])},
            request_factory=request_factory
        )

        call_args, call_kwargs = request_factory.call_args
        call_kwargs['content'] = [item async for item in call_kwargs['content']]

        assert call_args == (
            'GET',
            'path',
        )
        assert call_kwargs == {
            'content': [b'[{"a":"a"}]'],
            'params': httpx.QueryParams(),
            'headers': httpx.Headers({'content-type': 'application/json'}),
            'cookies': httpx.Cookies(),
        }


class BuildRequestTestCase(unittest.TestCase):
    def test_build_request_none(self):
        request_factory = Mock()
        build_request(
            operation=OperationModel('GET', 'path', {}, None, {}),
            actual_params={},
            request_factory=request_factory,
        )

        request_factory.assert_called_with(
            'GET',
            'path',
            content=None,
            params=QueryParams(),
            headers=Headers(),
            cookies=Cookies(),
        )

    def test_request_param_list_simple(self):
        request_factory = Mock()
        build_request(
            operation=OperationModel(
                'GET',
                'path',
                {'q_a': FullParam('a', ParamLocation.query, ParamStyle.form, False, 'q_a', List[str])},
                None,
                {},
            ),
            actual_params=dict(q_a=['hello', 'world']),
            request_factory=request_factory,
        )

        request_factory.assert_called_with(
            'GET',
            'path',
            content=None,
            params=QueryParams(a='hello,world'),
            headers=Headers(),
            cookies=Cookies(),
        )

    def test_request_param_list_exploded(self):
        request_factory = Mock()
        build_request(
            operation=OperationModel(
                'GET',
                'path',
                {'q_a': FullParam('a', ParamLocation.query, ParamStyle.form, True, 'q_a', List[str])},
                None,
                {},
            ),
            actual_params=dict(q_a=['hello', 'world']),
            request_factory=request_factory
        )

        request_factory.assert_called_with(
            'GET',
            'path',
            content=None,
            params=QueryParams([('a', 'hello'), ('a', 'world')]),
            headers=Headers(),
            cookies=Cookies(),
        )
