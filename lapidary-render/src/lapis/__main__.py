import logging
from pathlib import Path

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
):
    logger.info('Load schema')
    doc = load_schema(schema_path)
    logger.info('Parse schema')
    tree = OpenApiModel(**doc)
    render_client(tree, target_directory, package_name)


def load_schema(schema_path: Path):
    import pickle
    cache_path = schema_path.with_suffix('.pickle')
    if cache_path.exists():
        with open(cache_path, 'br') as fb:
            return pickle.load(fb)

    with open(schema_path, 'rt') as f:
        import yaml
        doc = yaml.safe_load(f)

    with open(cache_path, 'wb') as fb:
        pickle.dump(doc, fb)
    return doc


if __name__ == '__main__':
    typer.run(main)
