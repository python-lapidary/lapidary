import sys
from typing import Annotated, Optional, Union

import pytest
from typing_extensions import Self

from lapidary.runtime import ClientBase, Query, Responses
from lapidary.runtime.model.op import OperationModel, get_operation_model


def test_optional_param():
    class Client(ClientBase):
        async def operation(
            self: Self,
            param: Annotated[Optional[str], Query()],
        ) -> Annotated[None, Responses({})]:
            pass

    op = get_operation_model('GET', '/op', Client.operation)
    expected_anno = Query()
    expected_anno.supply_formal('param', Optional[str])
    assert op == OperationModel('GET', '/op', {'param': expected_anno}, {})


def test_union_param():
    class Client(ClientBase):
        async def operation(
            self: Self,
            param: Annotated[Union[str, None], Query()],
        ) -> Annotated[None, Responses({})]:
            pass

    op = get_operation_model('GET', '/op', Client.operation)
    expected_anno = Query()
    expected_anno.supply_formal('param', Optional[str])
    assert op == OperationModel('GET', '/op', {'param': expected_anno}, {})


@pytest.mark.skipif(sys.version_info < (3, 10), reason='type-or requires python3.10 or higher')
def test_or_none_param():
    class Client(ClientBase):
        async def operation(
            self: Self,
            param: Annotated[str | None, Query()],
        ) -> Annotated[None, Responses({})]:
            pass

    op = get_operation_model('GET', '/op', Client.operation)
    expected_anno = Query()
    expected_anno.supply_formal('param', Optional[str])
    assert op == OperationModel('GET', '/op', {'param': expected_anno}, {})
