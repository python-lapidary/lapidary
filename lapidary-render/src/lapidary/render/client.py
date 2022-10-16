import logging
from pathlib import Path

from jinja2 import Environment

from .elems import ResolverFunc, get_client_class_module
from .module_path import ModulePath
from .render import render
from ..config import Config
from ..openapi import model as openapi

logger = logging.getLogger(__name__)


def render_client_module(
        model: openapi.OpenApiModel, config: Config, gen_root: Path, resolver: ResolverFunc, env: Environment
):
    root_mod = ModulePath(config.package)
    client_module_path = root_mod / 'client.py'
    file_path = client_module_path.to_path(gen_root)
    logger.info('Render client module to %s', file_path)

    client_class_module = get_client_class_module(model, client_module_path, root_mod, resolver)
    render(client_class_module, 'client_module.py.jinja2', file_path, env, config.format)
