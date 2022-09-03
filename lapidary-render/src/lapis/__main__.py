import logging
from pathlib import Path

import typer

from lapis.openapi.model import OpenApiModel
from lapis.render import render_client

logging.basicConfig()
logger = logging.getLogger('lapis')
logger.setLevel(logging.INFO)


def main(
        schema_path: str,
        target_directory: Path,
        package_name: str,
):
    doc = load_schema(schema_path)
    tree = OpenApiModel(**doc)
    render_client(tree, target_directory, package_name)


def load_schema(schema_path):
    with open(schema_path, 'rt') as f:
        import yaml
        doc = yaml.safe_load(f)
    return doc


if __name__ == '__main__':
    typer.run(main)
