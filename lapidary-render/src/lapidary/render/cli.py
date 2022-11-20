import logging
from pathlib import Path

import typer

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
        project_root: Path = typer.Argument(Path('.')),
        format_: bool = typer.Option(True, '--format/--no-format'),
        cache: bool = True
):
    """Update existing project. Read configuration from pyproject.yaml ."""

    if not project_root.exists():
        logger.error(f"'Target '{project_root}' doesn't exists'")
        raise typer.Exit(code=1)

    from .main import update_project
    from .config import load_config

    try:
        config = load_config(project_root)
    except (KeyError, FileNotFoundError):
        raise SystemExit('Missing Lapidary configuration')

    config.format = format_
    config.cache = cache
    update_project(project_root, config)


@app.command()
def init(
        schema_path: Path,
        project_root: Path,
        package_name: str,
        format_: bool = typer.Option(True, '--format/--no-format'),
        render: bool = True,
):
    """Create a new project from scratch."""

    if project_root.exists():
        logger.error(f'Target "{project_root}" exists')
        raise typer.Exit(code=1)

    from .main import init_project

    init_project(schema_path, project_root, package_name, format_, render)
