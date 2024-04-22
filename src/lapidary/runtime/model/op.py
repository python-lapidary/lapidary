import dataclasses as dc
import inspect

import httpx
import typing_extensions as typing

from ..response import find_type, parse_model
from .params import ParameterAnnotation, RequestPartHandler, find_annotations, process_params
from .response_map import ResponseMap, Responses

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

        obj: typing.Any = parse_model(response, typ)

        if isinstance(obj, Exception):
            raise obj
        else:
            return obj


def get_response_map(return_anno: type) -> ResponseMap:
    annos = find_annotations(return_anno, Responses)
    if len(annos) != 1:
        raise TypeError('Operation function must have exactly one Responses annotation')

    return annos[0].responses


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
