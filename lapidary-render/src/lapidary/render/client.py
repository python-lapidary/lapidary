import concurrent.futures
import logging
import os
from pathlib import Path

from jinja2 import Environment, PackageLoader

from lapidary.runtime import openapi
from lapidary.runtime.model.refs import get_resolver
from lapidary.runtime.module_path import ModulePath
from .config import Config
from .model import get_auth_module, get_client_class_module, render_schema_modules
from .render import render

logger = logging.getLogger(__name__)


# Use factory because its cache isn't pickable.
def environment() -> Environment:
    return Environment(
        keep_trailing_newline=True,
        loader=PackageLoader("lapidary.render"),
    )


def render_client(model: openapi.OpenApiModel, target: Path, config: Config) -> None:
    gen_root = target / config.gen_root
    resolver = get_resolver(model, config.package)
    root_mod = ModulePath(config.package)
    pkg_path = root_mod.to_path(gen_root, False)
    client_module = get_client_class_module(model, root_mod / 'client', root_mod, resolver)
    auth_module = get_auth_module(model, root_mod)
    format_ = config.format

    with (
        concurrent.futures.ProcessPoolExecutor() as executor
    ):
        init_future = executor.submit(render, 'init/init.py.jinja2', pkg_path / '__init__.py', environment, format_)
        client_future = executor.submit(render, 'client/client.py.jinja2', pkg_path / 'client.py', environment, format_, model=client_module)
        stub_future = executor.submit(render, 'client/client.pyi.jinja2', pkg_path / 'client.pyi', environment, format_, model=client_module)
        auth_future = executor.submit(render, 'auth/auth.py.jinja2', pkg_path / 'auth.py', environment, format_, model=auth_module, module=root_mod)
        schema_futures = render_schema_modules(model, config, gen_root, resolver, environment, executor)

        for f in [*schema_futures, client_future, auth_future, stub_future, init_future]:
            f.result()

    ensure_init_py(pkg_path)
    (pkg_path / 'py.typed').touch()
    logger.info('Done.')


def ensure_init_py(pkg_path: Path) -> None:
    for (dirpath, _, filenames) in os.walk(pkg_path):
        if '__init__.py' not in filenames:
            (Path(dirpath) / '__init__.py').touch()
