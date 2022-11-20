import logging
from pathlib import Path
from typing import Callable
from typing_extensions import TypeAlias

from jinja2 import Environment

from .black import format_code

logger = logging.getLogger(__name__)

EnvFactory: TypeAlias = Callable[[], Environment]


def render(source: str, destination: Path, env: EnvFactory, format_: bool, **kwargs) -> None:
    """Pass kwargs to jinja2 render"""

    logger.info('Render %s to %s', source, destination)
    try:
        code = env().get_template(source).render(**kwargs)
    except Exception:
        logger.info('Failed to render %s', destination)
        raise

    if format_:
        try:
            code = format_code(code)
        except Exception:
            logger.warning('Failed to format %s', destination)
            raise

    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with open(destination, 'wt') as fb:
            fb.write(code)
    except Exception:
        logger.info('Failed to save %s', destination)
        raise
