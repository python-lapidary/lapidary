import logging
from importlib import resources
from pathlib import Path

import tomlkit
from pydantic import BaseModel, Extra

from ...openapi import model as openapi

logger = logging.getLogger(__name__)


class PyProject(BaseModel):
    name: str
    description: str
    version: str
    authors: list[str] = []

    class Config:
        extra = Extra.forbid


def get_pyproject(info: openapi.Info) -> PyProject:
    return PyProject(
        name=info.title,
        description=info.description or "",
        version=info.version,
    )


def render_pyproject(root: Path, model: PyProject) -> None:
    target = root / 'pyproject.toml'
    if target.exists():
        logger.info('pyproject.toml exists, skipping')
        return

    with resources.open_text('lapis.render.templates', 'pyproject.toml') as fbuf:
        d: dict = tomlkit.loads(fbuf.read())

    d.setdefault('tool', {}).setdefault('poetry', {}).update(model.dict())

    with open(target, 'tw') as fbuf:
        fbuf.write(tomlkit.dumps(d, True))
