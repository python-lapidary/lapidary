import dataclasses as dc
from collections.abc import Sequence

import httpx
import typing_extensions as typing

from ..response import find_type
from .annotations import NameTypeAwareAnnotation, ResponseBody, ResponseMap
from .request import RequestHandler
from .response import ResponseEnvelope, ResponseHandler

if typing.TYPE_CHECKING:
    from .request import RequestBuilder


@dc.dataclass
class OperationModel:
    method: str
    path: str
    params: typing.Mapping[str, NameTypeAwareAnnotation]
    response_map: ResponseMap

    def process_params(
        self,
        actual_params: typing.Mapping[str, typing.Any],
        request: 'RequestBuilder',
    ) -> None:
        for param_name, value in actual_params.items():
            param_handler = self.params[param_name]
            if isinstance(param_handler, RequestHandler):
                param_handler.apply_request(request, actual_params[param_name])
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
            handlers: Sequence[ResponseHandler] = [anno for anno in field_info.metadata if isinstance(anno, ResponseHandler)]
            assert len(handlers) == 1
            handler = handlers[0]
            if isinstance(handler, NameTypeAwareAnnotation):
                field_type = field_info.annotation
                assert field_type
                handler.supply_formal(field_name, field_type)
            handler.apply_response(response, fields)
        obj = typ.parse_obj(fields)
        # obj: typing.Any = parse_model(response, typ)

        if isinstance(obj, DefaultEnvelope):
            if isinstance(obj.body, Exception):
                raise obj.body
            return obj.body
        else:
            return obj


BodyT = typing.TypeVar('BodyT')


class DefaultEnvelope(ResponseEnvelope, typing.Generic[BodyT]):
    body: typing.Annotated[BodyT, ResponseBody()]
