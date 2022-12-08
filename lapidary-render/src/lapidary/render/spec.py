import logging
from importlib.metadata import version
from pathlib import Path
from typing import Optional

import platformdirs
import yaml
from jsonpatch import JsonPatch

from lapidary.runtime.load import load_yaml_cached
from .config import Config

logger = logging.getLogger(__name__)


def load_spec(project_root: Path, config: Config) -> dict:
    spec_path = project_root / config.src_root / 'openapi.yaml'
    cache_path = platformdirs.user_cache_path('lapidary', version=version('lapidary'))
    cache_path.mkdir(parents=True, exist_ok=True)

    logger.info('Load schema')
    spec_dict = load_yaml_cached(spec_path, cache_path, config.cache)

    if (patch := load_patches(project_root, cache_path, config)) is not None:
        spec_dict = patch.apply(spec_dict)

    return spec_dict


def load_patches(project_root: Path, cache_path, config: Config) -> Optional[JsonPatch]:
    if config.patches is None:
        return None
    patches_path = config.get_patches(project_root)
    if not patches_path.exists():
        return None
    if not patches_path.is_dir():
        raise NotADirectoryError(patches_path)
    logger.info('Load patches')
    return JsonPatch([
        op
        for p in patches_path.glob('**/*.yaml')
        for op in load_yaml_cached(p, cache_path, config.cache)
    ])


def save_spec(doc: dict, path: Path) -> None:
    with open(path, 'wt') as stream:
        yaml.safe_dump(doc, stream, allow_unicode=True)

