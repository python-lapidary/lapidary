import logging
import os
from pathlib import Path
from typing import Any

from jinja2 import Environment, PackageLoader

from .black import format_code
from .elems import modules as mod_name
from .elems.client_class import get_operations
from .elems.client_module import get_client_class_module
from .elems.pyproject import get_pyproject, render_pyproject
from .elems.refs import get_resolver, ResolverFunc
from .elems.request_body import get_request_body_module
from .elems.response_body import get_response_body_module
from .elems.schema_module import get_modules_for_components_schemas, get_param_model_classes_module
from .module_path import ModulePath
from ..openapi import model as openapi

logger = logging.getLogger(__name__)


def render(source: str, destination: Path, render_model: Any, env: Environment):
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        text = env.get_template(source).render(model=render_model)
        text = format_code(text)
        with open(destination, 'wt') as fb:
            fb.write(text)
    except Exception:
        print(destination)
        raise


def render_client(model: openapi.OpenApiModel, target: Path, package_name: str) -> None:
    env = Environment(
        keep_trailing_newline=True,
        loader=PackageLoader("lapis.render"),
    )

    render_pyproject(target, get_pyproject(model.info))

    gen_root = target / 'gen'
    gen_root.mkdir(parents=True, exist_ok=True)

    resolver = get_resolver(model, package_name)

    render_client_module(model, package_name, gen_root, resolver, env)
    render_schema_modules(model, package_name, gen_root, resolver, env)

    ensure_init_py(gen_root, package_name)


def render_client_module(model: openapi.OpenApiModel, package_name: str, gen_root: Path, resolver: ResolverFunc, env: Environment):
    logger.info('Render client modules')
    root_mod = ModulePath(package_name)
    client_module = root_mod / 'client.py'
    client_class_module = get_client_class_module(model, client_module, root_mod, resolver)
    path = client_module.to_path(gen_root)
    render('client_class.py.jinja2', path, client_class_module, env)


def render_schema_modules(model: openapi.OpenApiModel, package_name: str, gen_root: Path, resolver: ResolverFunc, env: Environment):
    root_module = ModulePath(package_name)

    if model.components.schemas:
        logger.info('Render schema modules')
        modules = get_modules_for_components_schemas(model.components.schemas, root_module / 'components' / 'schemas', resolver)
        for module in modules:
            render('schema_class.py.jinja2', module.path.to_path(gen_root).with_suffix('.py'), module, env)

    for path, path_item in model.paths.__root__.items():
        for tpl in get_operations(path_item, True):
            method, op = tpl
            op_root_module = root_module / 'paths' / op.operationId
            if op.parameters:
                module_path = op_root_module / mod_name.PARAM_MODEL
                mod = get_param_model_classes_module(op, module_path, resolver)
                render('schema_class.py.jinja2', module_path.to_path(gen_root).with_suffix('.py'), mod, env)
            if op.requestBody:
                module_path = op_root_module / mod_name.REQUEST_BODY
                mod = get_request_body_module(op, module_path, resolver)
                render('schema_class.py.jinja2', module_path.to_path(gen_root).with_suffix('.py'), mod, env)
            if op.responses:
                module_path = op_root_module / mod_name.RESPONSE_BODY
                mod = get_response_body_module(op, module_path, resolver)
                render('schema_class.py.jinja2', module_path.to_path(gen_root).with_suffix('.py'), mod, env)


def ensure_init_py(gen_root, package_name):
    for (dirpath, dirnames, filenames) in os.walk(gen_root / package_name):
        if '__init__.py' not in filenames:
            (Path(dirpath) / '__init__.py').touch()
