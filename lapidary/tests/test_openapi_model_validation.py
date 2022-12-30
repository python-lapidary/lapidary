from unittest import TestCase

from pydantic import ValidationError

from lapidary.runtime import openapi


def test_validate_model():
    openapi.OpenApiModel(
        openapi='3.0.3',
        info=openapi.Info(
            title='test',
            version='1',
        ),
        paths=openapi.Paths(),
    )


def test_validate_extended_model():
    openapi.OpenApiModel(
        openapi='3.0.3',
        info=openapi.Info(
            title='test',
            version='1',
        ),
        paths=openapi.Paths(),
        **{'x-test-key': 'test-value'}
    )


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
    openapi.Paths()


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
