from typing import Annotated, Generic, Optional, Union

from client import ClientTestBase
from httpx import AsyncClient
from typing_extensions import Self, TypeVar

from lapidary.runtime import Body, ModelBase, Responses, get
from lapidary.runtime.model.op import process_operation_method


class BodyModel(ModelBase):
    a: Optional[str]


def test_serialize_str():
    class Client(ClientTestBase):
        def op(self: Self, body: Annotated[str, Body({'application/json': str})]) -> Annotated[None, Responses({})]:
            pass

    client = ClientTestBase(AsyncClient())

    adapter, response = process_operation_method(Client.op, get('/path'))
    request, auth = adapter.build_request(client, dict(body='a'))

    assert request.content == b'"a"'


def test_serialize_obj():
    class Client(ClientTestBase):
        def op(self: Self, body: Annotated[BodyModel, Body({'application/json': BodyModel})]) -> Annotated[None, Responses({})]:
            pass

    client = ClientTestBase(AsyncClient())

    adapter, response = process_operation_method(Client.op, get('/path'))
    request, auth = adapter.build_request(client, dict(body=BodyModel(a='a')))

    assert request.content == b'{"a":"a"}'


def test_serialize_list():
    class Client(ClientTestBase):
        def op(self: Self, body: Annotated[list[BodyModel], Body({'application/json': list[BodyModel]})]) -> Annotated[None, Responses({})]:
            pass

    client = ClientTestBase(AsyncClient())

    adapter, response = process_operation_method(Client.op, get('/path'))
    request, auth = adapter.build_request(client, dict(body=[BodyModel(a='a')]))

    assert request.content == b'[{"a":"a"}]'


T = TypeVar('T')


class GenericBodyModel(ModelBase, Generic[T]):
    a: T


def test_serialize_generic_str():
    class Client(ClientTestBase):
        def op(
            self: Self, body: Annotated[list[GenericBodyModel[str]], Body({'application/json': list[GenericBodyModel[str]]})]
        ) -> Annotated[None, Responses({})]:
            pass

    client = ClientTestBase(AsyncClient())

    adapter, response = process_operation_method(Client.op, get('/path'))
    request, auth = adapter.build_request(client, dict(body=[GenericBodyModel(a='a')]))

    assert request.content == b'[{"a":"a"}]'


def test_serialize_generic_int():
    class Client(ClientTestBase):
        def op(
            self: Self, body: Annotated[list[GenericBodyModel[int]], Body({'application/json': list[GenericBodyModel[int]]})]
        ) -> Annotated[None, Responses({})]:
            pass

    client = ClientTestBase(AsyncClient())

    adapter, response = process_operation_method(Client.op, get('/path'))
    request, auth = adapter.build_request(client, dict(body=[GenericBodyModel(a=1)]))

    assert request.content == b'[{"a":1}]'


def test_serialize_generic_obj():
    class Client(ClientTestBase):
        def op(
            self: Self, body: Annotated[list[GenericBodyModel[BodyModel]], Body({'application/json': list[GenericBodyModel[BodyModel]]})]
        ) -> Annotated[None, Responses({})]:
            pass

    client = ClientTestBase(AsyncClient())

    adapter, response = process_operation_method(Client.op, get('/path'))
    request, auth = adapter.build_request(client, dict(body=[GenericBodyModel(a=BodyModel(a='a'))]))

    assert request.content == b'[{"a":{"a":"a"}}]'


def test_serialize_generic_union():
    class Client(ClientTestBase):
        def op(
            self: Self,
            body: Annotated[
                Union[list[GenericBodyModel[BodyModel]], GenericBodyModel[BodyModel], BodyModel],
                Body({'application/json': Union[list[GenericBodyModel[BodyModel]], GenericBodyModel[BodyModel], BodyModel]}),
            ],
        ) -> Annotated[None, Responses({})]:
            pass

    client = ClientTestBase(AsyncClient())

    adapter, _ = process_operation_method(Client.op, get('/path'))

    request, _ = adapter.build_request(client, dict(body=[GenericBodyModel[BodyModel](a=BodyModel(a='a'))]))
    assert request.content == b'[{"a":{"a":"a"}}]'

    request, _ = adapter.build_request(client, dict(body=GenericBodyModel[BodyModel](a=BodyModel(a='a'))))
    assert request.content == b'{"a":{"a":"a"}}'

    request, _ = adapter.build_request(client, dict(body=BodyModel(a='a')))
    assert request.content == b'{"a":"a"}'
