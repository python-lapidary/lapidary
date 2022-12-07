import logging
from collections.abc import Iterable
from concurrent.futures import Executor, Future
from pathlib import Path

from lapidary.runtime import openapi, names as mod_name
from lapidary.runtime.model.refs import ResolverFunc
from lapidary.runtime.module_path import ModulePath

from .client_class import get_operations
from .request_body import get_request_body_module
from .response_body import get_response_body_module
from .schema_module import SchemaModule, get_modules_for_components_schemas, get_param_model_classes_module
from ..config import Config
from ..render import render, EnvFactory

logger = logging.getLogger(__name__)


def get_schema_modules(model: openapi.OpenApiModel, root_module: ModulePath, resolver: ResolverFunc) -> Iterable[SchemaModule]:
    if model.components.schemas:
        logger.info('Render schema modules')
        path = root_module / 'components' / 'schemas'
        yield from get_modules_for_components_schemas(model.components.schemas, path, resolver)

    for path, path_item in model.paths.__root__.items():
        for tpl in get_operations(path_item, True):
            _, op = tpl
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


def render_schema_modules(
        model: openapi.OpenApiModel, config: Config, gen_root: Path, resolver: ResolverFunc, env: EnvFactory,
        executor: Executor
) -> Iterable[Future]:
    return (
        executor.submit(render, 'schema_module.py.jinja2', mod.path.to_path(gen_root), env, config.format, model=mod)
        for mod in get_schema_modules(model, ModulePath(config.package), resolver)
    )
