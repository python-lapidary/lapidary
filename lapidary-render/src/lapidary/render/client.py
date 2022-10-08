from pathlib import Path

from jinja2 import Environment

from .elems import ResolverFunc, get_client_class_module
from .module_path import ModulePath
from .render import render
from ..config import Config
from ..openapi import model as openapi


def render_client_module(model: openapi.OpenApiModel, config: Config, gen_root: Path, resolver: ResolverFunc, env: Environment):
    root_mod = ModulePath(config.package)
    client_module_path = root_mod / 'client.py'
    client_class_module = get_client_class_module(model, client_module_path, root_mod, resolver)
    render(client_class_module, 'client_module.py.jinja2', client_module_path.path.to_path(gen_root), env, config.format)
