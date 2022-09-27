import unittest

from lapis.openapi import model as openapi
from lapis.render.elems.client_module import get_client_class_module
from lapis.render.elems.refs import get_resolver
from lapis.render.module_path import ModulePath


class GlobalHeadersTest(unittest.TestCase):
    def test_global_headers_in_output_model(self):
        model = openapi.OpenApiModel(
            openapi='3.0.3',
            info=openapi.Info(
                title='',
                version=''
            ),
            paths=openapi.Paths(__root__={}),
            lapis_headers_global={
                'user-agent': 'james-bond',
            }
        )

        module_path = ModulePath('test')
        module = get_client_class_module(model, module_path / 'client.py', module_path, get_resolver(model, 'test'))

        self.assertEqual(module.body.init_method.headers, [('user-agent', 'james-bond',)])
