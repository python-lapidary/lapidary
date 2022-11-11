import logging
from pathlib import Path

from jinja2 import Environment

from lapidary.runtime.module_path import ModulePath
from .client_module import ClientModule
from ..render import render



def render_auth_module(
        client_module: ClientModule, package_root: ModulePath, gen_root: Path,
        format_: bool, env: Environment
):
    file_path = (package_root / 'auth.py').to_path(gen_root)
    logger.info('Render auth module to %s', file_path)

    render(client_module, 'auth/auth.py.jinja2', file_path, env, format_)
