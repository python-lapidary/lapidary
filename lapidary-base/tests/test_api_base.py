import unittest
from unittest.mock import MagicMock

import httpx
import pydantic

from lapidary_base import ApiBase
from lapidary_base.response import _status_code_matches


class ApiBaseTest(unittest.TestCase):
    def test__status_code_matches(self):
        matches = [m for m in _status_code_matches('400')]
        self.assertEqual(['400', '40X', '4XX', 'default'], matches)

    def test_build_request_from_list(self):
        class RequestBodyModel(pydantic.BaseModel):
            a: str

        httpx_client = MagicMock(spec=httpx.AsyncClient)
        ApiBase(httpx_client)._build_request('GET', '/path/', request_body=[RequestBodyModel(a='a')])
        httpx_client.build_request.assert_called_with(
            'GET', '/path/', content='[{"a": "a"}]', params=None, headers=None, cookies=None
        )
