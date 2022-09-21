import logging
import pickle
from pathlib import Path
from typing import Optional

import typer
import yaml

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
    doc = load_spec(project_root, config)
    logger.info('Parse schema')
    model = OpenApiModel(**doc)
    render_client(model, project_root, config)
    return model


def load_spec(project_root: Path, config: Config):
    spec_path = project_root / config.specification
    errata_path = project_root / config.errata if config.errata is not None else None

    import hashlib
    digester = hashlib.new('sha224')

    with open(spec_path, 'rt') as fb:
        spec_text = fb.read()

    digester.update(spec_text.encode())

    if errata_path is not None:
        with open(errata_path, 'rt') as fb:
            errata_text = fb.read()
            digester.update(errata_text.encode())

    cache_path = project_root / '.cache' / Path(digester.hexdigest()).with_suffix('.pickle')
    if cache_path.exists():
        logger.info('Load spec from cache')
        with open(cache_path, 'br') as fb:
            return pickle.load(fb)

    # no up-to-date cache available

    logger.info('Parse spec')
    spec_dict = yaml.safe_load(spec_text)

    if errata_text is not None:
        logger.info('Parse errata')
        patch_dict = yaml.safe_load(errata_text)
        from jsonpatch import JsonPatch
        errata = JsonPatch(patch_dict)
        spec_dict = errata.apply(spec_dict)

    cache_path.parent.mkdir(exist_ok=True)
    with open(cache_path, 'wb') as fb:
        pickle.dump(spec_dict, fb)

    return spec_dict
