import unittest
from typing import Annotated

import httpx
import pydantic

from lapidary.runtime import ParamLocation
from lapidary.runtime._params import process_params
from lapidary.runtime.http_consts import CONTENT_TYPE, MIME_JSON
from lapidary.runtime.request import build_request


class BuildRequestTestCase(unittest.TestCase):
    def test_build_request_from_list(self):
        class RequestBodyModel(pydantic.BaseModel):
            a: str

        request_parts = build_request(
            param_model=None,
            request_body=[RequestBodyModel(a='a')],
            response_map=None,
            global_response_map=None,
        )

        self.assertEqual(
            dict(
                content='[{"a": "a"}]',
                params=None,
                headers=httpx.Headers({CONTENT_TYPE: MIME_JSON}),
                cookies=None,
            ),
            request_parts
        )

    def test_build_request_none(self):
        request = build_request(
            param_model=None, request_body=None, response_map=None, global_response_map=None
        )

        self.assertEqual(None, request['content'])

    def test_request_param_list_simple(self):
        class ParamModel(pydantic.BaseModel):
            a: Annotated[list[str], pydantic.Field(in_=ParamLocation.query)]

        query, _, _ = process_params(ParamModel(a=['hello', 'world']))
        self.assertEqual(['hello,world'], query.get_list('a'))

    def test_request_param_list_exploded(self):
        class ParamModel(pydantic.BaseModel):
            a: Annotated[list[str], pydantic.Field(in_=ParamLocation.query, explode=True)]

        query, _, _ = process_params(ParamModel(a=['hello', 'world']))
        self.assertEqual(['hello', 'world'], query.get_list('a'))
