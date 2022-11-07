import logging
from pathlib import Path

from lapidary.runtime.load import load_yaml_cached
from .config import Config

logger = logging.getLogger(__name__)


def load_spec(project_root: Path, config: Config) -> dict:
    spec_path = project_root / config.specification
    cache_path = project_root / '.lapidary_cache'
    cache_path.mkdir(exist_ok=True)

    logger.info('Load schema')
    spec_dict = load_yaml_cached(spec_path, cache_path, config.cache)

    if config.errata is not None:
        errata_path = project_root / config.errata
        if not errata_path.exists():
            raise ValueError("'Path doesn't exist", errata_path)
        logger.info('Load errata')
        if errata_path.is_dir():
            errata_dict = [
                op
                for p in errata_path.glob('**/*.yaml')
                for op in load_yaml_cached(p, cache_path, config.cache)
            ]
        else:
            errata_dict = load_yaml_cached(errata_path, cache_path, config.cache)
        from jsonpatch import JsonPatch
        errata = JsonPatch(errata_dict)
        spec_dict = errata.apply(spec_dict)

    return spec_dict
