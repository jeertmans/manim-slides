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

import click


@click.command(
    context_settings=dict(
        ignore_unknown_options=True, allow_extra_args=True, help_option_names=("-h",)
    ),
    options_metavar="[-h] [--CE|--GL]",
)
@click.option(
    "--CE",
    is_flag=True,
    envvar="MANIM_RENDERER",
    show_envvar=True,
    help="If set, use Manim Community Edition (CE) renderer. "
    "If this or ``--GL`` is not set, defaults to CE renderer.",
)
@click.option(
    "--GL",
    is_flag=True,
    envvar="MANIMGL_RENDERER",
    show_envvar=True,
    help="If set, use ManimGL renderer.",
)
@click.argument("args", metavar="[RENDERER_ARGS]...", nargs=-1, type=click.UNPROCESSED)
def render(ce: bool, gl: bool, args: tuple[str, ...]) -> None:
    """
    Render SCENE(s) from the input FILE, using the specified renderer.

    Use ``manim-slides render --help`` to see help information for
    a specific renderer.
    """
    if ce and gl:
        raise click.UsageError("You cannot specify both --CE and --GL renderers.")
    if gl:
        from importlib.metadata import version
        from importlib.util import find_spec

        if (
            version("manimgl") in ("1.7.1", "1.7.0")
            and "pyrr" not in sys.modules
            and find_spec("pyrr") is None
        ):
            import runpy
            from unittest.mock import MagicMock

            # ManimGL is broken because its imports a module that is not listed in its deps.
            # Furtunately, the imported code is unused, so we can mock it.
            # See patch: https://github.com/3b1b/manim/pull/2253/files.
            sys.modules["pyrr"] = MagicMock()
            sys.argv = ["manimlib", *args]
            runpy.run_module("manimlib", run_name="__main__", alter_sys=True)
        else:
            subprocess.run([sys.executable, "-m", "manimlib", *args])
    else:
        subprocess.run([sys.executable, "-m", "manim", "render", *args])
