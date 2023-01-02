from typing import cast
from unittest import TestCase

from pydantic import ValidationError

from lapidary.runtime import openapi


def test_validate_model():
    model = openapi.OpenApiModel(
        openapi='3.0.3',
        info=openapi.Info(
            title='test',
            version='1',
        ),
        paths=openapi.Paths(),
    )

    assert model.openapi == '3.0.3'
    assert model.info.title == 'test'
    assert model.info.version == '1'


def test_validate_extended_model():
    model = openapi.OpenApiModel(
        openapi='3.0.3',
        info=openapi.Info(
            title='test',
            version='1',
        ),
        paths=openapi.Paths(),
        **{'x-test-key': 'test-value'}
    )

    assert model.openapi == '3.0.3'
    assert model.openapi == '3.0.3'
    assert model.info.title == 'test'
    assert model.info.version == '1'
    assert model['x-test-key'] == 'test-value'


class TestValidation(TestCase):
    def test_validate_invalid_key(self):
        with self.assertRaises(ValidationError):
            openapi.OpenApiModel(
                openapi='3.0.3',
                info=openapi.Info(
                    title='test',
                    version='1',
                ),
                paths=openapi.Paths(),
                invalid_key='invalid-key',
            )

    def test_validate_invalid_value(self):
        """Make sure that root validator doesn't replace builtin validation"""
        with self.assertRaises(ValidationError):
            openapi.OpenApiModel(
                openapi='3.0.3',
                info=openapi.Info(
                    title='test',
                    version='1',
                ),
                paths='not-really',
            )

    def test_paths_invalid_key(self):
        with self.assertRaises(ValidationError):
            openapi.Paths(**{
                'invalid': openapi.PathItem()
            })

    def test_paths_invalid_value(self):
        with self.assertRaises(ValidationError):
            openapi.Paths(**{
                '/invalid': 'invalid-value'
            })


def test_validate_paths_noarg():
    model = openapi.Paths()

    assert model is not None
    assert len(model.items()) == 0


def test_validate_paths():
    paths = openapi.Paths(**{
        '/path': openapi.PathItem(),
        'x-extra': 'hello'
    })

    expected = {
        'x-extra': 'hello',
        '/path': openapi.PathItem().dict()
    }

    assert paths.dict() == expected

    assert paths.items() == {'/path': openapi.PathItem()}.items()
    assert paths['/path'] == openapi.PathItem()
    assert paths['x-extra'] == 'hello'


def test_validate_apikey_security():
    model = openapi.Components(
        securitySchemes=dict(
            t1=openapi.SecurityScheme(__root__=openapi.APIKeySecurityScheme(**{
                'type': openapi.Type1.apiKey,
                'name': 't1',
                'in': openapi.In4.header,
                'x-extra': 'test',
            }))
        )
    )

    assert model.securitySchemes['t1'].__root__['x-extra'] == 'test'


def test_validate_http_security():
    model = openapi.Components(
        securitySchemes=dict(
            t1=openapi.SecurityScheme(__root__=openapi.HTTPSecurityScheme(**{
                'scheme': 'basic',
                'type': openapi.Type2.http,
                'x-extra': 'test',
            }))
        )
    )

    assert model.securitySchemes['t1'].__root__['x-extra'] == 'test'


def test_validate_http_security_bearer():
    openapi.Components(
        securitySchemes=dict(
            t1=openapi.SecurityScheme(__root__=openapi.HTTPSecurityScheme(**{
                'scheme': 'bearer',
                'type': openapi.Type2.http,
                'bearerFormat': 'Bearer {token}'
            }))
        )
    )


class InvalidHTTPSecurity(TestCase):
    def test_non_bearer(self):
        with self.assertRaises(ValidationError):
            openapi.Components(
                securitySchemes=dict(
                    t1=openapi.SecurityScheme(__root__=openapi.HTTPSecurityScheme(**{
                        'scheme': 'basic',
                        'type': openapi.Type2.http,
                        'bearerFormat': 'Bearer {token}'
                    }))
                )
            )


class XORTestCase(TestCase):
    def test_media_type(self):
        with self.assertRaises(ValidationError):
            openapi.MediaType(
                example={'a': 'a'},
                examples={'a': openapi.Example(value={'a': 'a'})}
            )

    def test_schema(self):
        with self.assertRaises(ValidationError):
            openapi.Parameter(
                name='a',
                in_='path',
                schema_=openapi.Schema(),
                content={'a': openapi.MediaType()},
            )

    def test_style(self):
        with self.assertRaises(ValidationError):
            openapi.Parameter(
                name='a',
                in_='path',
                style='simple',
                content={'a': openapi.MediaType()},
            )

    def test_param_style(self):
        model = openapi.Parameter(
            name='a',
            in_='path',
            style='simple',
            schema=openapi.Schema(),
        )

        self.assertEqual('simple', model.style)

    def test_xor_validation(self):
        model = openapi.Parameter(**dict(
            name='test_param',
            in_='path',
            examples=dict(
                Example={}
            ),
        ))

        self.assertEqual(1, len(model.examples))


def test_validate_schema():
    doc = {
        'in': 'query',
        'name': 'format',
        'schema': {
            'type': 'string',
            'enum': ['json', 'xml'],
        },
    }
    model = openapi.Parameter.parse_obj(doc)

    assert model.schema_ is not None
    assert cast(openapi.Schema, model.schema_).type is openapi.Type.string
