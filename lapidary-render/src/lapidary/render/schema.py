import logging
from typing import Generator

from lapidary.runtime import names as mod_name
from lapidary.runtime.model import get_operations
from .elems import (
    get_request_body_module, get_response_body_module, SchemaModule,
    get_modules_for_components_schemas, get_param_model_classes_module,
)

logger = logging.getLogger(__name__)


def get_schema_modules(model, root_module, resolver) -> Generator[SchemaModule, None, None]:
    if model.components.schemas:
        logger.info('Render schema modules')
        path = root_module / 'components' / 'schemas'
        yield from get_modules_for_components_schemas(model.components.schemas, path, resolver)

    for path, path_item in model.paths.__root__.items():
        for tpl in get_operations(path_item, True):
            method, op = tpl
            op_root_module = root_module / 'paths' / op.operationId
            if op.parameters:
                mod = get_param_model_classes_module(op, op_root_module / mod_name.PARAM_MODEL, resolver)
                if len(mod.body) > 0:
                    yield mod
            if op.requestBody:
                mod = get_request_body_module(op, op_root_module / mod_name.REQUEST_BODY, resolver)
                if len(mod.body) > 0:
                    yield mod
            if len(op.responses.__root__):
                mod = get_response_body_module(op, op_root_module / mod_name.RESPONSE_BODY, resolver)
                if len(mod.body) > 0:
                    yield mod
