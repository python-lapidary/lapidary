import logging
from pathlib import Path
from typing import Optional

import typer

from lapis.openapi.model import OpenApiModel
from lapis.render import render_client

logging.basicConfig()
logger = logging.getLogger('lapis')
logger.setLevel(logging.INFO)


def main(
        schema_path: Path,
        target_directory: Path,
        package_name: str,
        errata: Optional[Path] = None,
):
    doc = load_schema(schema_path, errata)
    logger.info('Parse schema')
    tree = OpenApiModel(**doc)
    render_client(tree, target_directory, package_name)


def load_schema(schema_path: Path, errata_path: Optional[Path] = None):
    schema_mtime = schema_path.stat().st_mtime
    if errata_path is not None:
        schema_mtime = max(schema_mtime, errata_path.stat().st_mtime)
    cache_path = schema_path.with_suffix('.pickle')

    import pickle

    if cache_path.exists():
        cache_mtime = cache_path.stat().st_mtime
        if cache_mtime > schema_mtime:
            logger.info('Load spec from cache')
            with open(cache_path, 'br') as fb:
                return pickle.load(fb)

    logger.info('Load spec')
    with open(schema_path, 'rt') as f:
        import yaml
        doc = yaml.safe_load(f)

    if errata_path is not None:
        from .errata import load_errata
        errata = load_errata(errata_path)
        doc = errata.apply(doc)

    with open(cache_path, 'wb') as fb:
        pickle.dump(doc, fb)
    return doc


def start():
    typer.run(main)


if __name__ == '__main__':
    start()
