from typing import Callable

import click
from click import Context, Parameter

from .defaults import CONFIG_PATH
from .manim import logger


def config_path_option(function: Callable) -> Callable:
    """Wraps a function to add configuration path option."""
    return click.option(
        "-c",
        "--config",
        "config_path",
        metavar="FILE",
        default=CONFIG_PATH,
        type=click.Path(dir_okay=False),
        help="Set path to configuration file.",
        show_default=True,
    )(function)


def config_options(function: Callable) -> Callable:
    """Wraps a function to add configuration options."""
    function = config_path_option(function)
    function = click.option(
        "-f", "--force", is_flag=True, help="Overwrite any existing configuration file."
    )(function)
    function = click.option(
        "-m",
        "--merge",
        is_flag=True,
        help="Merge any existing configuration file with the new configuration.",
    )(function)
    return function


def verbosity_option(function: Callable) -> Callable:
    """Wraps a function to add verbosity option."""

    def callback(ctx: Context, param: Parameter, value: bool) -> None:

        if not value or ctx.resilient_parsing:
            return

        logger.setLevel(value)

    return click.option(
        "-v",
        "--verbosity",
        type=click.Choice(
            ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            case_sensitive=False,
        ),
        help="Verbosity of CLI output",
        default=None,
        expose_value=False,
        callback=callback,
    )(function)
