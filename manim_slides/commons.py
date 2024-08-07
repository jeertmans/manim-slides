from pathlib import Path
from typing import Any, Callable

import click
from click import Context, Parameter

from .defaults import CONFIG_PATH, FOLDER_PATH
from .logger import logger

F = Callable[..., Any]
Wrapper = Callable[[F], F]


def config_path_option(function: F) -> F:
    """Wrap a function to add configuration path option."""
    wrapper: Wrapper = click.option(
        "-c",
        "--config",
        "config_path",
        metavar="FILE",
        default=CONFIG_PATH,
        type=click.Path(dir_okay=False, path_type=Path),
        help="Set path to configuration file.",
        show_default=True,
    )
    return wrapper(function)


def config_options(function: F) -> F:
    """Wrap a function to add configuration options."""
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


def verbosity_option(function: F) -> F:
    """Wrap a function to add verbosity option."""

    def callback(ctx: Context, param: Parameter, value: str) -> None:
        if not value or ctx.resilient_parsing:
            return

        logger.setLevel(value)

    wrapper: Wrapper = click.option(
        "-v",
        "--verbosity",
        type=click.Choice(
            ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            case_sensitive=False,
        ),
        help="Verbosity of CLI output.",
        default=None,
        expose_value=False,
        envvar="MANIM_SLIDES_VERBOSITY",
        show_envvar=True,
        callback=callback,
    )

    return wrapper(function)


def folder_path_option(function: F) -> F:
    """Wrap a function to add folder path option."""

    def callback(ctx: Context, param: Parameter, value: Path) -> Path:
        if not value.exists():
            raise click.UsageError(
                f"Invalid value for '--folder': Directory '{value}' does not exist. "
                "Did you render the animations first?",
                ctx=ctx,
            )
        return value

    wrapper: Wrapper = click.option(
        "--folder",
        metavar="DIRECTORY",
        default=FOLDER_PATH,
        type=click.Path(file_okay=False, path_type=Path),
        callback=callback,
        help="Set slides folder.",
        show_default=True,
    )

    return wrapper(function)
