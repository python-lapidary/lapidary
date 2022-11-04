import concurrent.futures
import logging
import os
from pathlib import Path
from typing import Any

from jinja2 import Environment, PackageLoader

from .black import format_code
from .client import render_client_module
from .elems import get_resolver
from .schema import render_schema_modules
from ..openapi import model as openapi

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
        client_future = executor.submit(render_client_module, model, config, gen_root, resolver, env)
        schema_futures = render_schema_modules(model, config, gen_root, resolver, env, executor)

        for f in [*schema_futures, client_future]:
            f.result()

    ensure_init_py(gen_root, config.package)
    logger.info('Done.')


def ensure_init_py(gen_root, package_name):
    for (dirpath, dirnames, filenames) in os.walk(gen_root / package_name):
        if '__init__.py' not in filenames:
            (Path(dirpath) / '__init__.py').touch()
