import logging
from pathlib import Path
from typing import Any

from jinja2 import Environment

from .black import format_code

logger = logging.getLogger(__name__)


def render(render_model: Any, source: str, destination: Path, env: Environment, format_: bool) -> None:
    try:
        code = env.get_template(source).render(model=render_model)
    except Exception:
        logger.info('Failed to render %s', destination)
        raise

    if format_:
        try:
            code = format_code(code)
        except Exception:
            logger.info('Failed to format %s', destination)
            print(code)
            raise

    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with open(destination, 'wt') as fb:
            fb.write(code)
    except Exception:
        logger.info('Failed to save %s', destination)
        raise
