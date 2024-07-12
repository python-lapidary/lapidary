from typing import Annotated

import pytest

from lapidary.runtime import Header
from lapidary.runtime.model.annotations import find_annotation


def test_find_annotations():
    t = Annotated[int, Header()]
    typ, header = find_annotation(t, Header)
    assert typ is int
    assert isinstance(header, Header)


def test_find_annotations_class():
    t = Annotated[int, Header]
    typ, header = find_annotation(t, Header)
    assert typ is int
    assert isinstance(header, Header)


def test_find_annotations_multi():
    t = Annotated[int, Header, Header()]
    with pytest.raises(Exception):
        find_annotation(t, Header)
