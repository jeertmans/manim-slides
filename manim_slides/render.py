"""
Alias command to either
``manim render [OPTIONS] [ARGS]...`` or
``manimgl [OPTIONS] [ARGS]...``.

This is especially useful for two reasons:

1. You can are sure to execute the rendering command with the same Python environment
   as for ``manim-slides``.
2. You can pass options to the config.
"""

import sys

from typing import Tuple

import click


@click.command(
    context_settings=dict(ignore_unknown_options=True, allow_extra_args=True, help_option_names=("-h",)),
    options_metavar="[-h] [--CE|--GL]"
)
@click.option(
    "--CE",
    is_flag=True,
    envvar="MANIM_RENDERER",
    show_envvar=True,
    help="If set, use Manim Community Edition (CE) renderer. "
    "If this or --GL is not set, default to CE renderer.",
)
@click.option(
    "--GL",
    is_flag=True,
    envvar="MANIMGL_RENDERER",
    show_envvar=True,
    help="If set, use ManinGL renderer.",
)
@click.argument("args", metavar="[RENDERER_ARGS]...", nargs=-1, type=click.UNPROCESSED)
def render(ce: bool, gl: bool, args: Tuple[str, ...]) -> None:
    """
    Render SCENE(s) from the input FILE, using the specified renderer.

    Use 'manim-slides render --help' to see help information for
    a the specified renderer.
    """
    if ce and gl:
        raise click.UsageError("You cannot specify both --CE and --GL renderers.")
    if gl:
        from manimlib.__main__ import main

        sys.argv[0] = "manimgl"
        sys.argv[1:] = args

        main()
    else:
        from manim.cli.render.commands import render

        sys.argv[0] = "manim render"
        render.main(args)
