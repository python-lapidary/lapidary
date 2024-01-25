import dataclasses as dc
import inspect

import httpx

from .params import RequestPart, parse_params, find_annotations
from .response_map import ResponseMap, Responses
from ..compat import typing as ty
from ..response import find_type, parse_model

if ty.TYPE_CHECKING:
    from .request import RequestBuilder


@dc.dataclass(frozen=True)
class OperationModel:
    method: str
    path: str
    params: ty.Mapping[str, RequestPart]
    response_map: ResponseMap

    def process_params(
            self,
            actual_params: ty.Mapping[str, ty.Any],
            request: 'RequestBuilder',
    ) -> None:
        for param_name, param_handler in self.params.items():
            if param_name not in actual_params:
                continue

            param_handler.apply(request, actual_params[param_name])

    def handle_response(self, response: httpx.Response) -> ty.Any:
        """
        Possible special cases:
        Exception
        Auth
        """

        typ = find_type(response, self.response_map)

        if typ is None:
            return None

        obj: ty.Any = parse_model(response, typ)

        if '__metadata__' in dir(typ):
            for anno in typ.__metadata__:
                if callable(anno):
                    obj = anno(obj)

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
        fn: ty.Callable,
) -> OperationModel:
    sig = inspect.signature(fn)
    return OperationModel(
        method=method,
        path=path,
        params=parse_params(sig),
        response_map=get_response_map(sig.return_annotation),
    )
