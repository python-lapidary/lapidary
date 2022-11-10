import concurrent.futures
import functools
import logging
import os
from concurrent.futures import Executor, Future
from pathlib import Path
from typing import Any, Iterable

from jinja2 import Environment, PackageLoader

from lapidary.runtime import openapi
from lapidary.runtime.model.refs import get_resolver, ResolverFunc
from lapidary.runtime.module_path import ModulePath
from .black import format_code
from .config import Config
from .elems import get_client_class_module, ClientModule
from .elems.module import AbstractModule
from .schema import get_schema_modules

logger = logging.getLogger(__name__)


def render(render_model: Any, source: str, destination: Path, env: Environment, format_: bool) -> None:
    try:
        code = env.get_template(source).render(model=render_model)
    except Exception:
        logger.info('Failed to render %s', destination)
        raise

    if format_:
        try:
            code = format_code(code)
        except Exception:
            logger.info('Failed to format %s', destination)
            print(code)
            raise

    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with open(destination, 'wt') as fb:
            fb.write(code)
    except Exception:
        logger.info('Failed to save %s', destination)
        raise


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
        stub_future   = executor.submit(render_client_stub,   client_module, root_mod, gen_root, config.format, env)
        auth_future   = executor.submit(render_auth_module,   client_module, root_mod, gen_root, config.format, env)
        schema_futures = render_schema_modules(model, config, gen_root, resolver, env, executor)

        for f in [*schema_futures, client_future, auth_future, stub_future]:
            f.result()

    ensure_init_py(gen_root, config.package)
    logger.info('Done.')


def ensure_init_py(gen_root, package_name):
    for (dirpath, dirnames, filenames) in os.walk(gen_root / package_name):
        if '__init__.py' not in filenames:
            (Path(dirpath) / '__init__.py').touch()


def render_client_module(
        client_module: ClientModule, package_root: ModulePath,
        gen_root: Path, format_: bool, env: Environment
):
    file_path = (package_root / 'client.py').to_path(gen_root)
    logger.info('Render client module to %s', file_path)

    render(client_module, 'client/client.py.jinja2', file_path, env, format_)


def render_client_stub(
        client_module: ClientModule, package_root: ModulePath,
        gen_root: Path, format_: bool, env: Environment
):
    file_path = (package_root / 'client.pyi').to_path(gen_root)
    logger.info('Render client stub to %s', file_path)

    render(client_module, 'client/client.pyi.jinja2', file_path, env, format_)


def render_auth_module(
        client_module: ClientModule, package_root: ModulePath,
        gen_root: Path, format_: bool, env: Environment
):
    file_path = (package_root / 'auth.py').to_path(gen_root)
    logger.info('Render auth module to %s', file_path)

    render(client_module, 'auth/auth.py.jinja2', file_path, env, format_)


def render_schema_modules(
        model: openapi.OpenApiModel, config: Config, gen_root: Path, resolver: ResolverFunc, env: Environment,
        executor: Executor
) -> Iterable[Future]:
    fn = functools.partial(render_, 'schema_module.py.jinja2', env, gen_root, config.format)
    return [executor.submit(fn, x) for x in get_schema_modules(model, ModulePath(config.package), resolver)]


def render_(source: str, env: Environment, gen_root: Path, format_: bool, render_model: AbstractModule):
    render(render_model, source, render_model.path.to_path(gen_root), env, format_)
