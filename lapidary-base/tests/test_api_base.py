import unittest
from typing import Annotated
from unittest.mock import MagicMock

import httpx
import pydantic

import lapidary_base
from lapidary_base import ApiBase
from lapidary_base._params import process_params
from lapidary_base.http_consts import CONTENT_TYPE, MIME_JSON
from lapidary_base.response import _status_code_matches


class ApiBaseTest(unittest.TestCase):
    def test__status_code_matches(self):
        matches = [m for m in _status_code_matches('400')]
        self.assertEqual(['400', '40X', '4XX', 'default'], matches)

    def test_build_request_from_list(self):
        class RequestBodyModel(pydantic.BaseModel):
            a: str

        httpx_client = MagicMock(spec=httpx.AsyncClient)
        ApiBase(httpx_client)._build_request(
            'GET',
            '/path/',
            param_model=None,
            request_body=[RequestBodyModel(a='a')],
            response_map={},
        )
        httpx_client.build_request.assert_called_with(
            'GET',
            '/path/',
            content='[{"a": "a"}]',
            params=None,
            headers={CONTENT_TYPE: MIME_JSON},
            cookies=None,
        )

    def test_build_request_none(self):
        class ApiClient(ApiBase): pass

        client = ApiClient(httpx.AsyncClient())
        request = client._build_request(
            'GET', 'http://example.com/', param_model=None, request_body=None, response_map=None
        )

        self.assertEqual(b'', request.content)

    def test_request_param_list_simple(self):
        class ParamModel(pydantic.BaseModel):
            a: Annotated[list[str], pydantic.Field(in_=lapidary_base.ParamLocation.query, )]

        query, _, _ = process_params(ParamModel(a=['hello', 'world']))
        self.assertEqual(['hello,world'], query.get_list('a'))

    def test_request_param_list_exploded(self):
        class ParamModel(pydantic.BaseModel):
            a: Annotated[list[str], pydantic.Field(in_=lapidary_base.ParamLocation.query, explode=True)]

        query, _, _ = process_params(ParamModel(a=['hello', 'world']))
        self.assertEqual(['hello', 'world'], query.get_list('a'))
