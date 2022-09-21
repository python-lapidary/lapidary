import logging
from pathlib import Path
from typing import Optional

import typer

from .config import load_config, Config
from .openapi.model import OpenApiModel
from .render import render_client
from .render.elems.pyproject import render_pyproject, get_pyproject

logging.basicConfig()
logger = logging.getLogger('lapis')
logger.setLevel(logging.INFO)

app = typer.Typer()


@app.command()
def update(
        project_root: Path = Path('.')
):
    config = load_config(project_root / 'pyproject.toml')
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
    doc = load_schema(config.specification.resolve(project_root), config.errata)
    logger.info('Parse schema')
    model = OpenApiModel(**doc)
    render_client(model, project_root, config)
    return model


def load_schema(schema_path: Path, errata_path: Optional[Path] = None):
    schema_mtime = schema_path.stat().st_mtime
    if errata_path is not None:
        schema_mtime = max(schema_mtime, errata_path.stat().st_mtime)
    cache_path = schema_path.with_suffix('.pickle')

    import pickle

    if cache_path.exists():
        cache_mtime = cache_path.stat().st_mtime
        if cache_mtime > schema_mtime:
            logger.info('Load spec from cache')
            with open(cache_path, 'br') as fb:
                return pickle.load(fb)

    logger.info('Load spec')
    with open(schema_path, 'rt') as f:
        import yaml
        doc = yaml.safe_load(f)

    if errata_path is not None:
        from .errata import load_errata
        errata = load_errata(errata_path)
        doc = errata.apply(doc)

    with open(cache_path, 'wb') as fb:
        pickle.dump(doc, fb)
    return doc
