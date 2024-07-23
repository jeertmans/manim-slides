from pathlib import Path
from typing import Any, Callable

import click
from click import Context, Parameter

from ..core.config import list_presentation_configs
from ..core.defaults import CONFIG_PATH, FOLDER_PATH
from ..core.logger import logger

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
    wrapper: Wrapper = click.option(
        "--folder",
        metavar="DIRECTORY",
        default=FOLDER_PATH,
        type=click.Path(exists=True, file_okay=False, path_type=Path),
        help="Set slides folder.",
        show_default=True,
        is_eager=True,  # Needed to expose its value to other callbacks
    )

    return wrapper(function)


def scenes_argument(function: F) -> F:
    """
    Wrap a function to add a scenes arguments.

    This function assumes that :func:`folder_path_option` is also used
    on the same decorated function.
    """

    def callback(ctx: Context, param: Parameter, value: tuple[str]) -> list[Path]:
        folder: Path = ctx.params.get("folder")

        presentation_config_paths = list_presentation_configs(folder)
        scene_names = [path.stem for path in presentation_config_paths]
        num_scenes = len(scene_names)
        num_digits = len(str(num_scenes))

        if num_scenes == 0:
            raise click.UsageError(
                f"Folder {folder} does not contain "
                "any valid config file, did you render the animations first?"
            )

        paths = []

        if value:
            for scene_name in value:
                try:
                    i = scene_names.index(scene_name)
                    paths.append(presentation_config_paths[i])
                except ValueError:
                    raise click.UsageError(
                        f"Could not find scene `{scene_name}` in: "
                        + ", ".join(scene_names)
                        + ". Did you make a typo or forgot to render the animations first?"
                    ) from None
        else:
            click.echo(
                "Choose at least one or more scenes from "
                "(enter the corresponding number):\n"
                + "\n".join(
                    f"- {i:{num_digits}d}: {name}"
                    for i, name in enumerate(scene_names, start=1)
                )
            )
            continue_prompt = True
            while continue_prompt:
                index = click.prompt(
                    "Please enter a value", type=click.IntRange(1, num_scenes)
                )
                paths.append(presentation_config_paths[index - 1])
                continue_prompt = click.confirm(
                    "Do you want to enter an additional scene?"
                )

        return paths

    wrapper: Wrapper = click.argument("scenes", nargs=-1, callback=callback)

    return wrapper(function)
