import collections.abc
import typing

import typing_extensions

from lapidary.runtime.metattype import make_not_optional


def test_make_not_optional_str():
    assert make_not_optional(str) is str


def test_make_not_optional_typing_optional_str():
    assert make_not_optional(typing.Optional[str]) is str


def test_make_not_optional_typing_extensions_optional_str():
    assert make_not_optional(typing_extensions.Optional[str]) is str


def test_make_not_optional_iterable_str():
    assert make_not_optional(collections.abc.Iterable[str]) == collections.abc.Iterable[str]
