import functools
import logging
from collections.abc import Iterable
from concurrent.futures import Executor, Future
from pathlib import Path
from typing import Generator, Any

from jinja2 import Environment

from . import names as mod_name
from .elems import (
    get_operations, ResolverFunc, get_request_body_module, get_response_body_module, SchemaModule,
    get_modules_for_components_schemas, get_param_model_classes_module,
)
from .module_path import ModulePath
from .render import render
from ..config import Config
from ..openapi import model as openapi

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


def render_(source: str, env: Environment, gen_root: Path, format_: bool, render_model: Any):
    render(render_model, source, render_model.path.to_path(gen_root), env, format_)


def render_schema_modules(
        model: openapi.OpenApiModel, config: Config, gen_root: Path, resolver: ResolverFunc, env: Environment,
        executor: Executor
) -> Iterable[Future]:
    fn = functools.partial(render_, 'schema_module.py.jinja2', env, gen_root, config.format)
    return [executor.submit(fn, x) for x in get_schema_modules(model, ModulePath(config.package), resolver)]
