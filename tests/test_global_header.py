import unittest

import pydantic
from pydantic import ValidationError
from lapis.openapi import model as openapi


class MyTestCase(unittest.TestCase):
    def test_extra_prop_x(self):
        model: openapi.Components = pydantic.parse_obj_as(openapi.Components, {
            'x-lapis-headers-global': {
                'Accept': 'application/json; version=2.3.5'
            }
        })

        self.assertEqual(model.lapis_headers_global, {'Accept': 'application/json; version=2.3.5'})

    def test_extra_prop_non_x(self):
        def raises():
            pydantic.parse_obj_as(openapi.Components, {
                'y-lapis-headers-global': {
                    'Accept': 'application/json; version=2.3.5'
                }
            })

        self.assertRaises(ValidationError, raises)
