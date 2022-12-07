import logging
from importlib.metadata import version
from pathlib import Path

from jinja2 import Environment

from .config import Config, PYPROJ_TOML

logger = logging.getLogger(__name__)


def create_pyproj(project_root: Path, config: Config, title, env: Environment) -> None:
    text = env.get_template('pyproject.toml.jinja2').render(
        package=config.package,
        project_name=project_root.name,
        openapi_title=title,
        versions=dict(
            pydantic=version('pydantic'),
            lapidary=version('lapidary'),
            lapidary_render=version('lapidary-render'),
        )
    )
    with open(project_root / PYPROJ_TOML, 'wt') as stream:
        stream.write(text)


def update_pyproj(_1: Path, _2: Config):
    """
    Check dependency versions.
    If it's different from required, issue a warning;
    if it's missing, add one.
    """

    import warnings
    warnings.warn('Updating pyproject.toml is currently not supported.')
