from pathlib import Path
from typing import Any

from jinja2 import Environment

from .black import format_code


def render(render_model: Any, source: str, destination: Path, env: Environment, format_: bool) -> None:
    try:
        code = env.get_template(source).render(model=render_model)

        if format_:
            code = format_code(code)

        destination.parent.mkdir(parents=True, exist_ok=True)
        with open(destination, 'wt') as fb:
            fb.write(code)
    except Exception:
        print(destination)
        raise
