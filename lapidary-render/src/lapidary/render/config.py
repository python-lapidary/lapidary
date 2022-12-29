import dataclasses
from pathlib import Path

import tomli

PYPROJ_TOML = 'pyproject.toml'


@dataclasses.dataclass
class Config:
    package: str
    format_strict: bool = False
    cache: bool = True

    openapi_root: str = 'src/openapi'
    gen_root: str = 'gen'
    patches: str = 'patches'

    def get_patches(self, project_root: Path) -> Path:
        return project_root / self.openapi_root / self.patches

    def get_openapi(self, project_root: Path) -> Path:
        return project_root / self.openapi_root / 'openapi.yaml'


def load_config(project_root: Path) -> Config:
    pyproj_path = project_root / PYPROJ_TOML
    if not pyproj_path.exists():
        raise FileNotFoundError(pyproj_path)

    with open(pyproj_path, 'br') as fb:
        pyproj = tomli.load(fb)
    pyproj_dict = pyproj['tool']['lapidary']
    return Config(**pyproj_dict)
