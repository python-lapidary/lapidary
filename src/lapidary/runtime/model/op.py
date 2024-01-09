from collections.abc import Iterator
import dataclasses as dc
import inspect

import httpx

from .params import FullParam, Param, ParamLocation, ProcessedParams, serialize_param
from .request import RequestBody, RequestBodyModel
from .response_map import ResponseMap, Responses
from ..absent import ABSENT
from ..compat import typing as ty


@dc.dataclass(frozen=True)
class InputData:
    query: httpx.QueryParams
    headers: httpx.Headers
    cookies: httpx.Cookies
    path: ty.Mapping[str, str]
    request_body: ty.Any


@dc.dataclass(frozen=True)
class OperationModel:
    method: str
    path: str
    params: ty.Mapping[str, FullParam]
    request_body: ty.Optional[RequestBodyModel]
    response_map: ResponseMap

    def process_params(self, actual_params: ty.Mapping[str, ty.Any]) -> ProcessedParams:
        containers: ty.Mapping[ParamLocation, ty.List[ty.Any]] = {
            ParamLocation.cookie: [],
            ParamLocation.header: [],
            ParamLocation.query: [],
            ParamLocation.path: [],
        }
        request_body: ty.Any = None

        for param_name, value in actual_params.items():
            if self.request_body and param_name == self.request_body.param_name:
                request_body = value
                continue

            if isinstance(value, httpx.Auth):
                continue

            formal_param = self.params.get(param_name)
            if not formal_param:
                raise KeyError(param_name)

            if value is ABSENT:
                continue

            placement = formal_param.location

            value = [(formal_param.alias, value) for value in serialize_param(value, formal_param.style, formal_param.explode)]
            containers[placement].extend(value)

        return ProcessedParams(
            query=httpx.QueryParams(containers[ParamLocation.query]),
            headers=httpx.Headers(containers[ParamLocation.header]),
            cookies=httpx.Cookies(containers[ParamLocation.cookie]),
            path={item[0]: item[1] for item in containers[ParamLocation.path]},
            request_body=request_body,
        )


@dc.dataclass
class Operation:
    method: str
    path: str


def parse_params(sig: inspect.Signature) -> Iterator[ty.Union[FullParam, RequestBodyModel]]:
    for name, param in sig.parameters.items():
        anno = param.annotation

        if anno == ty.Self or (type(anno) is type and issubclass(anno, httpx.Auth)):
            continue

        if param.annotation == inspect.Parameter.empty:
            raise TypeError(f"Parameter '{name} is missing annotation'")

        param_annos = [a for a in anno.__metadata__ if isinstance(a, (Param, RequestBody))]
        if len(param_annos) != 1:
            raise ValueError(f'{param.name}: expected exactly one annotation of type RequestBody, ')

        param_anno = param_annos.pop()

        if isinstance(param_anno, RequestBody):
            yield RequestBodyModel(
                name,
                param_anno.content
            )
        else:
            yield FullParam(
                name=param.name,
                alias=param_anno.alias or param.name,
                location=param_anno.location,
                type=param.annotation,
                style=param_anno.get_style(),
                explode=param_anno.get_explode(),
            )


def get_response_map(return_anno: ty.Union[ty.Annotated, inspect.Signature.empty]) -> ResponseMap:
    annos = [anno for anno in return_anno.__metadata__ if isinstance(anno, Responses)]
    if len(annos) != 1:
        raise TypeError('Operation function must have exactly one Responses annotation')

    return annos.pop().responses


class LapidaryOperation(ty.Callable):
    lapidary_operation: Operation
    lapidary_operation_model: ty.Optional[OperationModel]


def get_operation_model(
        fn: LapidaryOperation,
) -> OperationModel:
    base_model: Operation = fn.lapidary_operation
    sig = inspect.signature(ty.cast(ty.Callable, fn))
    params = list(parse_params(sig))
    request_body_ = [param for param in params if isinstance(param, RequestBodyModel)]
    if len(request_body_) > 1:
        raise ValueError()
    request_body = request_body_.pop() if request_body_ else None

    return OperationModel(
        method=base_model.method,
        path=base_model.path,
        params={param.name: param for param in params if isinstance(param, (FullParam, httpx.Auth))},
        request_body=request_body,
        response_map=get_response_map(sig.return_annotation),
    )
