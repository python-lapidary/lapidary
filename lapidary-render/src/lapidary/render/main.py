import logging
from pathlib import Path
from typing import Optional

import typer

from lapidary.runtime import openapi
from .client import render_client
from .config import load_config, Config
from .elems import render_pyproject, get_pyproject
from .load import load_spec

logging.basicConfig()
logging.getLogger('lapidary').setLevel(logging.INFO)
logger = logging.getLogger(__name__)

app = typer.Typer()


@app.command()
def version():
    """Print version and exit."""

    from importlib.metadata import version
    package = 'lapidary'
    print(f'{package}, {version(package)}')


@app.command()
def update(
        project_root: Path = typer.Argument(Path('')),
        format_: bool = typer.Option(True, '--format/--no-format'),
        cache: bool = True
):
    """Update existing project. Read configuration from pyproject.yaml ."""

    config = load_config(project_root / 'pyproject.toml')
    config.format = format_
    config.cache = cache
    update_project(project_root, config)


@app.command()
def init(
        schema_path: Path,
        project_root: Path,
        package_name: str,
        errata: Optional[Path] = None,
):
    """Create a new project from scratch."""

    if project_root.exists():
        logger.error(f'Target "{project_root}" exists')
        raise typer.Exit(code=1)

    project_root.mkdir(parents=True, exist_ok=False)

    config = Config(
        package=package_name,
        errata=errata,
    )
    model = update_project(project_root, config)
    render_pyproject(project_root, get_pyproject(model.info), config)


def update_project(project_root: Path, config: Config) -> openapi.OpenApiModel:
    doc = load_spec(project_root, config)
    save_spec(doc, project_root / 'gen' / config.package / config.specification)

    logger.info('Prepare client model')
    model = openapi.OpenApiModel(**doc)
    render_client(model, project_root, config)
    return model


def save_spec(doc: dict, path: Path) -> None:
    import yaml
    with open(path, 'wt') as stream:
        yaml.safe_dump(doc, stream, allow_unicode=True)
