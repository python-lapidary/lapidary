import logging
from pathlib import Path
from typing import Optional

import typer

from .config import load_config, Config
from .load import load_spec
from .openapi.model import OpenApiModel
from .render import render_client
from .render.elems.pyproject import render_pyproject, get_pyproject

logging.basicConfig()
logger = logging.getLogger('lapidary')
logger.setLevel(logging.INFO)

app = typer.Typer()


@app.command()
def update(
        project_root: Path = Path('.'),
        format_: bool = typer.Option(True, '--format/--no-format'),
        cache: bool = True
):
    config = load_config(project_root / 'pyproject.toml')
    config.format = format_
    config.cache = cache
    update_project(project_root, config)


@app.command('init')
def init(
        schema_path: Path,
        package_name: str,
        project_root=Path('.'),
        errata: Optional[Path] = None,
):
    config = Config(
        specification=schema_path,
        package=package_name,
        errata=errata,
        format=True
    )
    model = update_project(project_root, config)
    render_pyproject(project_root, get_pyproject(model.info), config)


def update_project(project_root: Path, config: Config) -> OpenApiModel:
    doc = load_spec(project_root, config)
    logger.info('Prepare client model')
    model = OpenApiModel(**doc)
    render_client(model, project_root, config)
    return model
