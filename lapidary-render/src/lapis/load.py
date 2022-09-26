import pickle
from pathlib import Path

import yaml

from lapis.config import Config
from lapis.main import logger


def load_spec(project_root: Path, config: Config):
    spec_path = project_root / config.specification
    errata_path = project_root / config.errata if config.errata is not None else None

    import hashlib
    digester = hashlib.new('sha224')

    with open(spec_path, 'rt') as fb:
        spec_text = fb.read()

    if config.cache:
        digester.update(spec_text.encode())

    if errata_path is not None:
        with open(errata_path, 'rt') as fb:
            errata_text = fb.read()
            if config.cache:
                digester.update(errata_text.encode())

    cache_path = project_root / '.lapis_cache' / Path(digester.hexdigest()).with_suffix('.pickle')
    if config.cache and cache_path.exists():
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
