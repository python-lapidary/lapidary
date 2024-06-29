import sys
from collections.abc import Awaitable
from typing import Annotated, Optional, Union

import pytest
from typing_extensions import Self

from lapidary.runtime import ClientBase, Query, Responses
from lapidary.runtime.model.op import OperationModel


def test_optional_param():
    class Client(ClientBase):
        async def operation(
            self: Self,
            param: Annotated[Optional[str], Query()],
        ) -> Annotated[Awaitable[None], Responses({})]:
            pass

    op = OperationModel('GET', '/op', None, Client.operation)

    param = next(iter(op.params.values()))
    assert isinstance(param, Query)
    assert param._name == 'param'
    assert param._type == Optional[str]


def test_union_param():
    class Client(ClientBase):
        async def operation(
            self: Self,
            param: Annotated[Union[str, None], Query()],
        ) -> Annotated[Awaitable[None], Responses({})]:
            pass

    op = OperationModel(
        'GET',
        '/op',
        None,
        Client.operation,
    )

    param = next(iter(op.params.values()))
    assert isinstance(param, Query)
    assert param._name == 'param'
    assert param._type == Optional[str]


@pytest.mark.skipif(sys.version_info < (3, 10), reason='type-or requires python3.10 or higher')
def test_or_none_param():
    class Client(ClientBase):
        async def operation(
            self: Self,
            param: Annotated[str | None, Query()],
        ) -> Annotated[Awaitable[None], Responses({})]:
            pass

    op = OperationModel(
        'GET',
        '/op',
        None,
        Client.operation,
    )

    param = next(iter(op.params.values()))
    assert isinstance(param, Query)
    assert param._name == 'param'
    assert param._type == Optional[str]
