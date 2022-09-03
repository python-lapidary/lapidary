import dataclasses
import logging
import os
from functools import partial
from pathlib import Path
from pprint import pprint

from jinja2 import Environment, PackageLoader
from typing import Any

from .black import format_code
from .elems.module import get_schema_class_module, get_client_class_module
from .elems.pyproject import get_pyproject, render_pyproject
from .refs import resolve_ref, ResolverFunc
from ..openapi import model as openapi

logger = logging.getLogger(__name__)


def render(source: str, destination: Path, render_model: Any, env: Environment):
    try:
        text = env.get_template(source).render(model=render_model)
        text = format_code(text)
        with open(destination, 'wt') as fb:
            fb.write(text)
    except Exception:
        print(render_model)
        raise


def render_client(model: openapi.OpenApiModel, target: Path, package_name: str) -> None:
    env = Environment(
        keep_trailing_newline=True,
        loader=PackageLoader("lapis.render"),
    )

    render_pyproject(target, get_pyproject(model.info))

    gen_root = target / 'gen'
    package_dir = gen_root / package_name
    package_dir.mkdir(parents=True, exist_ok=True)

    resolver = partial(resolve_ref, model, package_name)

    render_client_module(model, package_name, gen_root, resolver, env)
    render_schema_modules(model, package_name, gen_root, resolver, env)

    for (dirpath, dirnames, filenames) in os.walk(package_dir):
        if '__init__.py' not in filenames:
            (Path(dirpath) / '__init__.py').touch()


def render_client_module(model: openapi.OpenApiModel, package_name: str, gen_root: Path, resolver: ResolverFunc, env: Environment):
    logger.info('Render client modules')
    client_class_module = get_client_class_module(model, package_name, resolver)
    path = gen_root.joinpath(*package_name.split('.'), 'api_client.py')
    render('client_class.py.jinja2', path, client_class_module, env)


def render_schema_modules(model: openapi.OpenApiModel, package_name: str, gen_root: Path, resolver: ResolverFunc, env: Environment):
    if model.components.schemas:
        logger.info('Render schema modules')
        for name, schema in model.components.schemas.items():
            render_schema_module(name, schema, package_name, gen_root, resolver, env)


def render_schema_module(name: str, schema: openapi.Schema, package_name: str, gen_root: Path, resolver: ResolverFunc, env: Environment):
    module = get_schema_class_module(schema, [package_name, 'components', 'schemas', name], resolver)
    path = gen_root.joinpath(*module.package.split('.'), module.name + '.py')
    path.parent.mkdir(parents=True, exist_ok=True)
    render('schema_class.py.jinja2', path, module, env)
