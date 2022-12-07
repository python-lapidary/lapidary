import hashlib
import pickle
from pathlib import Path

import yaml

from .openapi import model as openapi


def load_yaml_cached(path: Path, cache_root: Path, use_cache: bool) -> dict:
    with open(path, 'rt') as fb:
        text = fb.read()

    return load_yaml_cached_(text, cache_root, use_cache)


def load_yaml_cached_(text: str, cache_root: Path, use_cache: bool) -> dict:
    do_cache = use_cache and len(text) > 50_000
    if do_cache:
        digest = hashlib.sha224(text.encode()).hexdigest()
        cache_path = (cache_root / digest).with_suffix('.pickle' + str(pickle.HIGHEST_PROTOCOL))
        if cache_path.exists():
            with open(cache_path, 'br') as fb:
                return pickle.load(fb)

    d = yaml.safe_load(text)
    if do_cache:
        with open(cache_path, 'bw') as fb:
            pickle.dump(d, fb, pickle.HIGHEST_PROTOCOL)

    return d


def load_model(mod: str) -> openapi.OpenApiModel:
    from importlib.resources import open_text
    import sys
    module = sys.modules[mod]
    with open_text(module, 'openapi.yaml') as stream:
        text = stream.read()

    import platformdirs
    d = load_yaml_cached_(text, platformdirs.user_cache_path(), True)
    return openapi.OpenApiModel.parse_obj(d)
