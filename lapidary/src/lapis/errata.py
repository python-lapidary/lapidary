from pathlib import Path
from jsonpatch import JsonPatch
import yaml


def load_errata(path: Path) -> JsonPatch:
    with open(path, 'rt') as fb:
        patch_dict = yaml.safe_load(fb)
    patch = JsonPatch(patch_dict)
    return patch
