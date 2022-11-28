import logging
import shutil
from pathlib import Path

import yaml

from lapidary.runtime import openapi
from .client import render_client, environment
from .config import Config
from .pyproj import create_pyproj
from .spec import load_spec, save_spec

logger = logging.getLogger(__name__)


def init_project(
        schema_path: Path,
        project_root: Path,
        package_name: str,
        format_: bool,
        render: bool,
):
    # Create a new project from scratch
    # - Init directories
    # - Create pyproject.toml
    # - Copy openapi file to root/src
    # - Call update_project

    assert not project_root.exists()

    config = Config(
        package=package_name,
        format=format_,
    )

    project_root.mkdir()
    (project_root / config.src_root).mkdir()
    (project_root / config.gen_root).mkdir()

    shutil.copyfile(schema_path, config.get_openapi(project_root))
    with open(config.get_openapi(project_root), 'rt') as buf:
        oa_doc = yaml.safe_load(buf)

    create_pyproj(project_root, config,oa_doc['info']['title'], environment())

    if render:
        render_client_(project_root, config, oa_doc)


def update_project(project_root: Path, config: Config) -> None:
    # update_pyproj(project_root, config)

    shutil.rmtree(project_root / config.gen_root)
    (project_root / config.gen_root).mkdir()
    oa_doc = update_openapi(project_root, config)
    render_client_(project_root, config, oa_doc)


def update_openapi(project_root: Path, config: Config) -> dict:
    doc = load_spec(project_root, config)
    package_path = project_root / config.gen_root / config.package
    package_path.mkdir()
    save_spec(doc, package_path / 'openapi.yaml')
    return doc


def render_client_(project_root: Path, config: Config, oa_doc: dict) -> None:
    logger.info('Prepare elems model')
    model = openapi.OpenApiModel.parse_obj(oa_doc)
    render_client(model, project_root, config)
