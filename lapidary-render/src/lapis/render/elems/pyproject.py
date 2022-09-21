import logging
from importlib import resources
from pathlib import Path

import tomlkit
from pydantic import BaseModel, Extra

from ...config import Config
from ...openapi import model as openapi
from importlib.metadata import version

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


def render_pyproject(root: Path, model: PyProject, config: Config) -> None:
    target = root / 'pyproject.toml'
    if target.exists():
        with open(target) as fbuf:
            text = fbuf.read()
    else:
        with resources.open_text('lapis.render.templates', 'pyproject.toml') as fbuf:
            text = fbuf.read()

    d: dict = tomlkit.loads(text)

    update_poetry_config(d, model)
    update_lapis_config(d, config)

    with open(target, 'tw') as fbuf:
        fbuf.write(tomlkit.dumps(d, True))


def update_poetry_config(d: dict, model: PyProject):
    poetry = d.setdefault('tool', {}).setdefault('poetry', {})
    poetry.update(model.dict())
    deps = poetry.setdefault('dependencies', {})
    deps['lapis-client-base'] = '^' + version('lapis-client-base')


def update_lapis_config(d: dict, model: Config) -> None:
    lapis_config = d.setdefault('tool', {}).setdefault('lapis', {})
    lapis_config.update(model.dict(exclude_none=True, exclude_unset=True))
