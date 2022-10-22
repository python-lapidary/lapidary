import logging
import shutil
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
def version():
    """Print version and exit."""

    from importlib.metadata import version
    package = 'lapidary'
    print(f'{package}, {version(package)}')


@app.command()
def update(
        project_root: Path = typer.Argument(Path('.')),
        format_: bool = typer.Option(True, '--format/--no-format'),
        cache: bool = True
):
    """Update existing project. Read configuration from pyproject.yaml ."""

    config = load_config(project_root / 'pyproject.toml')
    config.format = format_
    config.cache = cache
    update_project(project_root, config)


@app.command('init')
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

    target_schema_file_name = Path('openapi').with_suffix(schema_path.suffix)
    target_schema = project_root / target_schema_file_name
    project_root.mkdir(parents=True, exist_ok=False)

    logger.info('Copying %s to %s', schema_path, target_schema)
    shutil.copy2(schema_path, target_schema)

    config = Config(
        package=package_name,
        errata=errata,
    )
    model = update_project(project_root, config)
    render_pyproject(project_root, get_pyproject(model.info), config)


def update_project(project_root: Path, config: Config) -> OpenApiModel:
    doc = load_spec(project_root, config)
    logger.info('Prepare client model')
    model = OpenApiModel(**doc)
    render_client(model, project_root, config)
    return model
