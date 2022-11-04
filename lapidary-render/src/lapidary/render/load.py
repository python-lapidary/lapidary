import hashlib
import logging
import pickle
from pathlib import Path

import yaml

from lapidary.config import Config

logger = logging.getLogger(__name__)


def load_yaml_cached(path: Path, cache_root: Path, use_cache: bool) -> dict:
    with open(path, 'rt') as fb:
        text = fb.read()

    do_cache = use_cache and path.stat().st_size > 50_000
    if do_cache:
        digest = hashlib.sha224(text.encode()).hexdigest()
        cache_path = (cache_root / digest).with_suffix('.pickle')
        if cache_path.exists():
            with open(cache_path, 'br') as fb:
                return pickle.load(fb)

    d = yaml.safe_load(text)
    if do_cache:
        with open(cache_path, 'bw') as fb:
            pickle.dump(d, fb)

    return d


def load_spec(project_root: Path, config: Config) -> dict:
    spec_path = project_root / config.specification
    errata_path = project_root / config.errata if config.errata is not None else None
    cache_path = project_root / '.lapidary_cache'
    cache_path.mkdir(exist_ok=True)

    logger.info('Load schema')
    spec_dict = load_yaml_cached(spec_path, cache_path, config.cache)

    if errata_path is not None:
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
