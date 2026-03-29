from typing import Annotated, Generic, Union

import httpx
from typing_extensions import Self, TypeVar

from lapidary import Body, ModelBase, Responses
from lapidary.operation import process_operation_method


class BodyModel(ModelBase):
    a: str | None


client = httpx.AsyncClient()
base_url = 'https://example.com'


def test_serialize_str():
    class Client:
        def op(self: Self, body: Annotated[str, Body({'application/json': str})]) -> Annotated[None, Responses({})]:
            pass

    adapter, response = process_operation_method(Client.op, 'GET', '/path')
    request = adapter.build_request(client.build_request, base_url, dict(body='a'))

    assert request.content == b'"a"'


def test_serialize_obj():
    class Client:
        def op(self: Self, body: Annotated[BodyModel, Body({'application/json': BodyModel})]) -> Annotated[None, Responses({})]:
            pass

    adapter, response = process_operation_method(Client.op, 'GET', '/path')
    request = adapter.build_request(client.build_request, base_url, dict(body=BodyModel(a='a')))

    assert request.content == b'{"a":"a"}'


def test_serialize_list():
    class Client:
        def op(self: Self, body: Annotated[list[BodyModel], Body({'application/json': list[BodyModel]})]) -> Annotated[None, Responses({})]:
            pass

    adapter, response = process_operation_method(Client.op, 'GET', '/path')
    request = adapter.build_request(client.build_request, base_url, dict(body=[BodyModel(a='a')]))

    assert request.content == b'[{"a":"a"}]'


T = TypeVar('T')


class GenericBodyModel(ModelBase, Generic[T]):
    a: T


def test_serialize_generic_str():
    class Client:
        def op(
            self: Self, body: Annotated[list[GenericBodyModel[str]], Body({'application/json': list[GenericBodyModel[str]]})]
        ) -> Annotated[None, Responses({})]:
            pass

    adapter, response = process_operation_method(Client.op, 'GET', '/path')
    request = adapter.build_request(client.build_request, base_url, dict(body=[GenericBodyModel(a='a')]))

    assert request.content == b'[{"a":"a"}]'


def test_serialize_generic_int():
    class Client:
        def op(
            self: Self, body: Annotated[list[GenericBodyModel[int]], Body({'application/json': list[GenericBodyModel[int]]})]
        ) -> Annotated[None, Responses({})]:
            pass

    adapter, response = process_operation_method(Client.op, 'GET', '/path')
    request = adapter.build_request(client.build_request, base_url, dict(body=[GenericBodyModel(a=1)]))

    assert request.content == b'[{"a":1}]'


def test_serialize_generic_obj():
    class Client:
        def op(
            self: Self, body: Annotated[list[GenericBodyModel[BodyModel]], Body({'application/json': list[GenericBodyModel[BodyModel]]})]
        ) -> Annotated[None, Responses({})]:
            pass

    adapter, response = process_operation_method(Client.op, 'GET', '/path')
    request = adapter.build_request(client.build_request, base_url, dict(body=[GenericBodyModel(a=BodyModel(a='a'))]))

    assert request.content == b'[{"a":{"a":"a"}}]'


def test_serialize_generic_union():
    class Client:
        def op(
            self: Self,
            body: Annotated[
                Union[list[GenericBodyModel[BodyModel]], GenericBodyModel[BodyModel], BodyModel],
                Body({'application/json': Union[list[GenericBodyModel[BodyModel]], GenericBodyModel[BodyModel], BodyModel]}),
            ],
        ) -> Annotated[None, Responses({})]:
            pass

    adapter, _ = process_operation_method(Client.op, 'GET', '/path')

    request = adapter.build_request(client.build_request, base_url, dict(body=[GenericBodyModel[BodyModel](a=BodyModel(a='a'))]))
    assert request.content == b'[{"a":{"a":"a"}}]'

    request = adapter.build_request(client.build_request, base_url, dict(body=GenericBodyModel[BodyModel](a=BodyModel(a='a'))))
    assert request.content == b'{"a":{"a":"a"}}'

    request = adapter.build_request(client.build_request, base_url, dict(body=BodyModel(a='a')))
    assert request.content == b'{"a":"a"}'
