import dataclasses as dc
import inspect
from collections.abc import Sequence
from typing import Union

import httpx
import typing_extensions as typing

from ..response import find_type
from .params import ParameterAnnotation, RequestPartHandler, find_annotations, process_params
from .response import DefaultEnvelope, PropertyAnnotation, ResponseEnvelope, ResponseMap, ResponsePartHandler, Responses

if typing.TYPE_CHECKING:
    from .request import RequestBuilder


@dc.dataclass
class OperationModel:
    method: str
    path: str
    params: typing.Mapping[str, ParameterAnnotation]
    response_map: ResponseMap

    def process_params(
        self,
        actual_params: typing.Mapping[str, typing.Any],
        request: 'RequestBuilder',
    ) -> None:
        for param_name, value in actual_params.items():
            param_handler = self.params[param_name]
            if isinstance(param_handler, RequestPartHandler):
                param_handler.apply(request, actual_params[param_name])
            else:
                raise TypeError(param_name, type(value))

    def handle_response(self, response: httpx.Response) -> typing.Any:
        """
        Possible special cases:
        Exception
        Auth
        """

        typ = find_type(response, self.response_map)

        if typ is None:
            return None

        fields: typing.MutableMapping[str, typing.Any] = {}
        for field_name, field_info in typ.model_fields.items():
            handlers: Sequence[Union[ResponsePartHandler, type[ResponsePartHandler]]] = [
                anno
                for anno in field_info.metadata
                if isinstance(anno, ResponsePartHandler) or (inspect.isclass(anno) and issubclass(anno, ResponsePartHandler))
            ]
            assert len(handlers) == 1
            handler = handlers[0]
            if isinstance(handler, PropertyAnnotation):
                field_type = field_info.annotation
                assert field_type
                handler.supply_formal(field_name, field_type)
            handler.apply(fields, response)
        obj = typ.parse_obj(fields)
        # obj: typing.Any = parse_model(response, typ)

        if isinstance(obj, DefaultEnvelope):
            if isinstance(obj.body, Exception):
                raise obj.body
            return obj.body
        else:
            return obj


def get_response_map(return_anno: type) -> ResponseMap:
    annos: typing.Sequence[Responses] = find_annotations(return_anno, Responses)
    if len(annos) != 1:
        raise TypeError('Operation function must have exactly one Responses annotation')

    responses = annos[0].responses
    for media_type_map in responses.values():
        for media_type, typ in media_type_map.items():
            if not issubclass(typ, ResponseEnvelope):
                media_type_map[media_type] = DefaultEnvelope[typ]  # type: ignore[valid-type]
    return responses


def get_operation_model(
    method: str,
    path: str,
    fn: typing.Callable,
) -> OperationModel:
    sig = inspect.signature(fn)
    return OperationModel(
        method=method,
        path=path,
        params=process_params(sig),
        response_map=get_response_map(sig.return_annotation),
    )
