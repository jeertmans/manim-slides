"""
Alias command to either
``manim render [OPTIONS] [ARGS]...`` or
``manimgl [OPTIONS] [ARGS]...``.

This is especially useful for two reasons:

1. You can are sure to execute the rendering command with the same Python environment
   as for ``manim-slides``.
2. You can pass options to the config.
"""

import subprocess
import sys
from typing import Tuple

import click

from .logger import logger


@click.command(
    context_settings=dict(ignore_unknown_options=True, help_option_names=("-h",))
)
@click.option(
    "--CE",
    is_flag=True,
    envvar="MANIM_RENDERER",
    show_envvar=True,
    help="If set, use Manim Community Edition (CE) renderer. "
    "If this or --CE is not set, default to CE renderer.",
)
@click.option(
    "--GL",
    is_flag=True,
    envvar="MANIMGL_RENDERER",
    show_envvar=True,
    help="If set, use ManinGL renderer.",
)
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
def render(ce: bool, gl: bool, args: Tuple[str, ...]) -> None:
    """
    Render SCENE(s) from the input FILE, using the specified renderer.

    Use 'manim-slides render --help' to see help information for
    a the specified renderer.
    """
    if ce and gl:
        raise click.UsageError("You cannot specify both --CE and --GL renderers.")
    if gl:
        p_args = [sys.executable, "-m", "manimlib", *args]
        logger.debug(f"Rendering using ManimGL: {p_args}")
        subprocess.run(p_args)
    else:
        from manim.cli.render.commands import render

        logger.debug(f"Rendering using ManimCE: {args}")
        render.main(args)
