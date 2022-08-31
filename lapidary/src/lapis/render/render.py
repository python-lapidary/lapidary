import dataclasses
import os
from functools import partial
from pathlib import Path
from pprint import pprint
from typing import Any

from jinja2 import Environment, PackageLoader

from .elems.module import get_schema_class_module, get_client_class_module
from .elems.pyproject import get_pyproject, render_pyproject
from .refs import resolve_ref
from ..openapi.model import OpenApiModel


def render(source: str, destination: Path, render_model: Any, env: Environment):
    try:
        text = env.get_template(source).render(model=render_model)
        with open(destination, 'wt') as fb:
            fb.write(text)
    except Exception as x:
        print(render_model)
        raise


def render_client(model: OpenApiModel, target: Path, package_name: str) -> None:
    env = Environment(
        keep_trailing_newline=True,
        loader=PackageLoader("lapis.render"),
    )

    render_pyproject(target, get_pyproject(model.info))

    gen_root = target / 'gen'
    package_dir = gen_root / package_name
    package_dir.mkdir(parents=True, exist_ok=True)

    client_class_module = get_client_class_module(model, package_name)
    pprint(dataclasses.asdict(client_class_module))
    render('client_class.py.jinja2', package_dir / 'api_client.py', client_class_module, env)

    resolver = partial(resolve_ref, model, package_name)

    if model.components.schemas:
        for name, schema in model.components.schemas.items():
            module = get_schema_class_module(schema, [package_name, 'components', 'schemas', name], resolver)
            pprint(dataclasses.asdict(module))

            path = gen_root.joinpath(*module.package.split('.'), module.name + '.py')
            path.parent.mkdir(parents=True, exist_ok=True)

            render('schema_class.py.jinja2', path, module, env)

    for (dirpath, dirnames, filenames) in os.walk(package_dir):
        if '__init__.py' not in filenames:
            (Path(dirpath) / '__init__.py').touch()
