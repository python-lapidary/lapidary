import unittest

from lapidary.runtime import openapi
from lapidary.runtime.model import get_resolver, get_client_model
from lapidary.runtime.module_path import ModulePath


class GlobalHeadersTest(unittest.TestCase):
    def test_global_headers_in_output_model(self):
        model = openapi.OpenApiModel(
            openapi='3.0.3',
            info=openapi.Info(
                title='',
                version=''
            ),
            paths=openapi.Paths(),
            lapidary_headers_global={
                'user-agent': 'james-bond',
            }
        )

        module_path = ModulePath('test')
        client_model = get_client_model(model, module_path, get_resolver(model, 'test'))

        self.assertEqual([('user-agent', 'james-bond',)], client_model.init_method.headers)
