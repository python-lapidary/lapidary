import logging
import os
from pathlib import Path
from typing import Any

from jinja2 import Environment, PackageLoader

from .black import format_code
from .elems import modules as mod_name
from .elems.client_class import get_operations
from .elems.client_module import get_client_class_module
from .elems.refs import get_resolver, ResolverFunc
from .elems.request_body import get_request_body_module
from .elems.response_body import get_response_body_module
from .elems.schema_module import get_modules_for_components_schemas, get_param_model_classes_module
from .module_path import ModulePath
from ..config import Config
from ..openapi import model as openapi

logger = logging.getLogger(__name__)


def render(source: str, destination: Path, render_model: Any, env: Environment, config: Config):
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        text = env.get_template(source).render(model=render_model)
        if config.format:
            text = format_code(text)
        with open(destination, 'wt') as fb:
            fb.write(text)
    except Exception:
        print(destination)
        raise


def render_client(model: openapi.OpenApiModel, target: Path, config: Config) -> None:
    env = Environment(
        keep_trailing_newline=True,
        loader=PackageLoader("lapidary.render"),
    )

    gen_root = target / 'gen'
    gen_root.mkdir(parents=True, exist_ok=True)

    resolver = get_resolver(model, config.package)

    render_client_module(model, config, gen_root, resolver, env)
    render_schema_modules(model, config, gen_root, resolver, env)

    ensure_init_py(gen_root, config.package)


def render_client_module(model: openapi.OpenApiModel, config: Config, gen_root: Path, resolver: ResolverFunc, env: Environment):
    logger.info('Render client modules')
    root_mod = ModulePath(config.package)
    client_module = root_mod / 'client.py'
    client_class_module = get_client_class_module(model, client_module, root_mod, resolver)
    path = client_module.to_path(gen_root)
    render('client_module.py.jinja2', path, client_class_module, env, config)


def render_schema_modules(model: openapi.OpenApiModel, config: Config, gen_root: Path, resolver: ResolverFunc, env: Environment):
    root_module = ModulePath(config.package)

    if model.components.schemas:
        logger.info('Render schema modules')
        modules = get_modules_for_components_schemas(model.components.schemas, root_module / 'components' / 'schemas', resolver)
        for module in modules:
            render('schema_module.py.jinja2', module.path.to_path(gen_root), module, env, config)

    for path, path_item in model.paths.__root__.items():
        for tpl in get_operations(path_item, True):
            method, op = tpl
            op_root_module = root_module / 'paths' / op.operationId
            if op.parameters:
                module_path = op_root_module / mod_name.PARAM_MODEL
                mod = get_param_model_classes_module(op, module_path, resolver)
                if len(mod.body) > 0:
                    render('schema_module.py.jinja2', module_path.to_path(gen_root), mod, env, config)
            if op.requestBody:
                module_path = op_root_module / mod_name.REQUEST_BODY
                mod = get_request_body_module(op, module_path, resolver)
                if len(mod.body) > 0:
                    render('schema_module.py.jinja2', module_path.to_path(gen_root), mod, env, config)
            if len(op.responses.__root__):
                module_path = op_root_module / mod_name.RESPONSE_BODY
                mod = get_response_body_module(op, module_path, resolver)
                if len(mod.body) > 0:
                    render('schema_module.py.jinja2', module_path.to_path(gen_root), mod, env, config)


def ensure_init_py(gen_root, package_name):
    for (dirpath, dirnames, filenames) in os.walk(gen_root / package_name):
        if '__init__.py' not in filenames:
            (Path(dirpath) / '__init__.py').touch()
