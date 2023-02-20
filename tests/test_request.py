import unittest
from typing import List
from unittest.mock import Mock

import httpx
import pydantic
from httpx import QueryParams, Headers, Cookies

from lapidary.runtime import ParamLocation
from lapidary.runtime.model import OperationModel, Param
from lapidary.runtime.model.params import ParamStyle
from lapidary.runtime.request import build_request


class BuildRequestTestCase(unittest.TestCase):
    def test_build_request_from_list(self) -> None:
        class RequestBodyModel(pydantic.BaseModel):
            a: str

        request_factory = Mock()
        build_request(
            operation=OperationModel('GET', 'path', [], {}, None),
            actual_params={},
            request_body=[RequestBodyModel(a='a')],
            response_map=None,
            global_response_map=None,
            request_factory=request_factory
        )

        request_factory.assert_called_with(
            'GET',
            'path',
            content='[{"a": "a"}]',
            params=None,
            headers=httpx.Headers({'content-type': 'application/json'}),
            cookies=None,
        )

    def test_build_request_none(self):
        request_factory = Mock()
        build_request(
            operation=OperationModel('GET', 'path', [], {}, None),
            actual_params={},
            request_body=None,
            response_map=None,
            global_response_map=None,
            request_factory=request_factory,
        )

        request_factory.assert_called_with(
            'GET',
            'path',
            content=None,
            params=None,
            headers=None,
            cookies=None,
        )

    def test_request_param_list_simple(self):
        request_factory = Mock()
        build_request(
            operation=OperationModel('GET', 'path', [Param('q_a', 'a', ParamLocation.query, List[str], ParamStyle.form, False)], {}, None),
            actual_params=dict(q_a=['hello', 'world']), request_body=None, response_map=None, global_response_map=None,
            request_factory=request_factory
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
            operation=OperationModel('GET', 'path', [Param('q_a', 'a', ParamLocation.query, List[str], ParamStyle.form, True)], {}, None),
            actual_params=dict(q_a=['hello', 'world']), request_body=None, response_map=None, global_response_map=None,
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
