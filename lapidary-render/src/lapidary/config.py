from pathlib import Path
from typing import Optional

import tomli
from pydantic import BaseSettings


class Config(BaseSettings):
    specification = Path('spec.yaml')
    package: str
    errata: Optional[Path] = None
    format = True
    cache = True


def load_config(config_path: Path) -> Config:
    if not config_path.exists():
        raise FileNotFoundError(config_path)

    with open(config_path, 'br') as fb:
        pyproject = tomli.load(fb)
        try:
            config_dict = pyproject['tool']['lapidary']
        except KeyError:
            raise SystemExit('Lapidary not configured for the project')
        return Config(**config_dict)
