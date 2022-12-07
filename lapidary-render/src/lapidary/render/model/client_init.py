from typing import Optional, Annotated

from lapidary.runtime import openapi
from lapidary.runtime.model.refs import ResolverFunc
from lapidary.runtime.model.type_hint import TypeHint
from lapidary.runtime.module_path import ModulePath
from pydantic import BaseModel, Field

from .operation_function import get_response_types_


class ClientInit(BaseModel):
    base_url: Optional[str]
    response_types: Annotated[set[TypeHint], Field(default_factory=set)]
    """ApiResponses types to import in the client module."""


def get_client_init(openapi_model: openapi.OpenApiModel, module: ModulePath, resolve: ResolverFunc) -> ClientInit:
    base_url = next(iter(openapi_model.servers)).url if openapi_model.servers and len(openapi_model.servers) > 0 else None

    response_types = get_response_types_(
        'LapidaryGlobalResponses',
        openapi_model.lapidary_responses_global,
        module,
        resolve,
    ) if openapi_model.lapidary_responses_global else set()

    return ClientInit(
        base_url=base_url,
        response_types=response_types,
    )
