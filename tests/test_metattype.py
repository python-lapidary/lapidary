import collections.abc
import typing

import pytest
import typing_extensions

from lapidary.runtime.metattype import make_not_optional


def test_make_not_optional_str():
    assert make_not_optional(str) is str


@pytest.mark.parametrize(
    'typ',
    [
        typing.Optional[str],  # noqa: UP045
        typing_extensions.Optional[str],  # noqa: UP045
        str | None,
    ],
)
def test_make_not_optional_typing_optional_str(typ: type):
    assert make_not_optional(typ) is str


def test_make_not_optional_iterable_str():
    assert make_not_optional(collections.abc.Iterable[str]) == collections.abc.Iterable[str]
