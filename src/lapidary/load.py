import hashlib
import logging
import pickle
from pathlib import Path

import yaml

from lapidary.config import Config

logger = logging.getLogger(__name__)


def load_as_dict(path: Path, cache_root: Path) -> dict:
    with open(path, 'rt') as fb:
        text = fb.read()
    digest = hashlib.sha224(text.encode()).hexdigest()
    cache_path = (cache_root / digest).with_suffix('.pickle')
    if cache_path.exists():
        with open(cache_path, 'br') as fb:
            return pickle.load(fb)

    d = yaml.safe_load(text)
    with open(cache_path, 'bw') as fb:
        pickle.dump(d, fb)

    return d


def load_spec(project_root: Path, config: Config) -> dict:
    spec_path = project_root / config.specification
    errata_path = project_root / config.errata if config.errata is not None else None
    cache_path = project_root / '.lapidary_cache'
    cache_path.mkdir(exist_ok=True)

    logger.info('Load schema')
    spec_dict = load_as_dict(spec_path, cache_path)

    if errata_path is not None:
        logger.info('Load errata')
        errata_dict = load_as_dict(errata_path, cache_path)
        from jsonpatch import JsonPatch
        errata = JsonPatch(errata_dict)
        spec_dict = errata.apply(spec_dict)

    return spec_dict
