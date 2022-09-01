import re
from pathlib import Path

from black import WriteBack, Mode, Report, get_sources, DEFAULT_INCLUDES
from black.concurrency import reformat_many


def format_code(root: Path, src: Path) -> None:
    import click
    ctx = click.Context(command=click.Command(name=''), obj=dict(root=root))

    report = Report(quiet=True)
    reformat_many(
        sources=get_sources(
            ctx=ctx, src=(str(src),), quiet=False, verbose=False, include=re.compile(DEFAULT_INCLUDES), exclude=None, extend_exclude=None,
            force_exclude=None, report=report, stdin_filename=None,
        ),
        fast=False,
        write_back=WriteBack.YES,
        mode=Mode(),
        report=report,
        workers=None,
    )
