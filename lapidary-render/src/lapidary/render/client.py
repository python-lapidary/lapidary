import concurrent.futures
import logging
import os
from pathlib import Path

from jinja2 import Environment, PackageLoader

from lapidary.runtime import openapi
from lapidary.runtime.model.refs import get_resolver
from lapidary.runtime.module_path import ModulePath
from .config import Config
from .elems import get_client_class_module, render_auth_module, render_client_module, render_client_stub, render_schema_modules

logger = logging.getLogger(__name__)


def render_client(model: openapi.OpenApiModel, target: Path, config: Config) -> None:
    env = Environment(
        keep_trailing_newline=True,
        loader=PackageLoader("lapidary.render"),
    )

    gen_root = target / 'gen'
    gen_root.mkdir(parents=True, exist_ok=True)

    resolver = get_resolver(model, config.package)

    with (
        concurrent.futures.ProcessPoolExecutor() as executor
    ):
        root_mod = ModulePath(config.package)
        client_module = get_client_class_module(model, root_mod / 'client', root_mod, resolver)
        client_future = executor.submit(render_client_module, client_module, root_mod, gen_root, config.format, env)
        stub_future = executor.submit(render_client_stub, client_module, root_mod, gen_root, config.format, env)
        auth_future = executor.submit(render_auth_module, client_module, root_mod, gen_root, config.format, env)
        schema_futures = render_schema_modules(model, config, gen_root, resolver, env, executor)

        for f in [*schema_futures, client_future, auth_future, stub_future]:
            f.result()

    ensure_init_py(gen_root, config.package)
    logger.info('Done.')


def ensure_init_py(gen_root, package_name):
    for (dirpath, dirnames, filenames) in os.walk(gen_root / package_name):
        if '__init__.py' not in filenames:
            (Path(dirpath) / '__init__.py').touch()
