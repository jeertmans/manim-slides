import signal
import sys
from pathlib import Path
from typing import Literal, Optional

import click
from click import Context, Parameter
from pydantic import ValidationError

from ..commons import config_path_option, folder_path_option, verbosity_option
from ..config import Config, PresentationConfig
from ..logger import logger


@click.command()
@folder_path_option
@click.help_option("-h", "--help")
@verbosity_option
def list_scenes(folder: Path) -> None:
    """List available scenes."""
    for i, scene in enumerate(_list_scenes(folder), start=1):
        click.secho(f"{i}: {scene}", fg="green")


def _list_scenes(folder: Path) -> list[str]:
    """List available scenes in given directory."""
    scenes = []

    for filepath in folder.glob("*.json"):
        try:
            _ = PresentationConfig.from_file(filepath)
            scenes.append(filepath.stem)
        except (
            Exception
        ) as e:  # Could not parse this file as a proper presentation config
            logger.warning(
                f"Something went wrong with parsing presentation config `{filepath}`: {e}"
            )

    logger.debug(f"Found {len(scenes)} valid scene configuration files in `{folder}`.")

    return scenes


def prompt_for_scenes(folder: Path) -> list[str]:
    """Prompt the user to select scenes within a given folder."""
    scene_choices = dict(enumerate(_list_scenes(folder), start=1))

    for i, scene in scene_choices.items():
        click.secho(f"{i}: {scene}", fg="green")

    click.echo()

    click.echo("Choose number corresponding to desired scene/arguments.")
    click.echo("(Use comma separated list for multiple entries)")

    def value_proc(value: Optional[str]) -> list[str]:
        indices = list(map(int, (value or "").strip().replace(" ", "").split(",")))

        if not all(0 < i <= len(scene_choices) for i in indices):
            raise click.UsageError("Please only enter numbers displayed on the screen.")

        return [scene_choices[i] for i in indices]

    if len(scene_choices) == 0:
        raise click.UsageError(
            "No scenes were found, are you in the correct directory?"
        )

    while True:
        try:
            scenes = click.prompt("Choice(s)", value_proc=value_proc)
            return scenes  # type: ignore
        except ValueError as e:
            raise click.UsageError(str(e)) from None


def get_scenes_presentation_config(
    scenes: list[str], folder: Path
) -> list[PresentationConfig]:
    """Return a list of presentation configurations based on the user input."""
    if len(scenes) == 0:
        scenes = prompt_for_scenes(folder)

    presentation_configs = []
    for scene in scenes:
        config_file = folder / f"{scene}.json"
        if not config_file.exists():
            raise click.UsageError(
                f"File {config_file} does not exist, check the scene name and make sure to use Slide as your scene base class"
            )
        try:
            presentation_configs.append(PresentationConfig.from_file(config_file))
        except ValidationError as e:
            raise click.UsageError(str(e)) from None

    return presentation_configs


def start_at_callback(
    ctx: Context, param: Parameter, values: str
) -> tuple[Optional[int], ...]:
    if values == "(None, None)":
        return (None, None)

    def str_to_int_or_none(value: str) -> Optional[int]:
        if value.lower().strip() == "":
            return None
        else:
            try:
                return int(value)
            except ValueError:
                raise click.BadParameter(
                    f"start index can only be an integer or an empty string, not `{value}`",
                    ctx=ctx,
                    param=param,
                ) from None

    values_tuple = values.split(",")
    n_values = len(values_tuple)
    if n_values == 2:
        return tuple(map(str_to_int_or_none, values_tuple))

    raise click.BadParameter(
        f"exactly 2 arguments are expected but you gave {n_values}, "
        "please use commas to separate them",
        ctx=ctx,
        param=param,
    )


@click.command()
@click.argument("scenes", nargs=-1)
@config_path_option
@folder_path_option
@click.option("--start-paused", is_flag=True, help="Start paused.")
@click.option(
    "-F",
    "--full-screen",
    "--fullscreen",
    "full_screen",
    is_flag=True,
    help="Toggle full screen mode.",
)
@click.option(
    "-s",
    "--skip-all",
    is_flag=True,
    help="Skip all slides, useful the test if slides are working. "
    "Automatically sets ``--exit-after-last-slide`` to True.",
)
@click.option(
    "--exit-after-last-slide",
    is_flag=True,
    help="At the end of last slide, the application will be exited.",
)
@click.option(
    "-H",
    "--hide-mouse",
    is_flag=True,
    help="Hide mouse cursor.",
)
@click.option(
    "--aspect-ratio",
    type=click.Choice(["keep", "ignore"], case_sensitive=False),
    default="keep",
    help="Set the aspect ratio mode to be used when rescaling the video.",
    show_default=True,
)
@click.option(
    "--sa",
    "--start-at",
    "start_at",
    metavar="<SCENE,SLIDE>",
    type=str,
    callback=start_at_callback,
    default=(None, None),
    help="Start presenting at (x, y), equivalent to ``--sacn x --sasn y``, "
    "and overrides values if not None.",
)
@click.option(
    "--sacn",
    "--start-at-scene-number",
    "start_at_scene_number",
    metavar="INDEX",
    type=int,
    default=0,
    help="Start presenting at a given scene number (0 is first, -1 is last).",
)
@click.option(
    "--sasn",
    "--start-at-slide-number",
    "start_at_slide_number",
    metavar="INDEX",
    type=int,
    default=0,
    help="Start presenting at a given slide number (0 is first, -1 is last).",
)
@click.option(
    "-S",
    "--screen",
    "screen_number",
    metavar="NUMBER",
    type=int,
    default=None,
    help="Present content on the given screen (a.k.a. display).",
)
@click.option(
    "--playback-rate",
    metavar="RATE",
    type=float,
    default=1.0,
    help="Playback rate of the video slides, see PySide6 docs for details. "
    " The playback rate of each slide is defined as the product of its default "
    " playback rate and the provided value.",
)
@click.option(
    "--next-terminates-loop",
    "next_terminates_loop",
    is_flag=True,
    help="If set, pressing next will turn any looping slide into a play slide.",
)
@click.option(
    "--hide-info-window",
    flag_value="always",
    help="Hide info window. By default, hide the info window if there is only one screen.",
)
@click.option(
    "--show-info-window",
    "hide_info_window",
    flag_value="never",
    help="Force to show info window.",
)
@click.option(
    "--info-window-screen",
    "info_window_screen_number",
    metavar="NUMBER",
    type=int,
    default=None,
    help="Put info window on the given screen (a.k.a. display). "
    "If there is more than one screen, it will by default put the info window "
    "on a different screen than the main player.",
)
@click.help_option("-h", "--help")
@verbosity_option
def present(  # noqa: C901
    scenes: list[str],
    config_path: Path,
    folder: Path,
    start_paused: bool,
    full_screen: bool,
    skip_all: bool,
    exit_after_last_slide: bool,
    hide_mouse: bool,
    aspect_ratio: str,
    start_at: tuple[Optional[int], Optional[int], Optional[int]],
    start_at_scene_number: int,
    start_at_slide_number: int,
    screen_number: Optional[int],
    playback_rate: float,
    next_terminates_loop: bool,
    hide_info_window: Optional[Literal["always", "never"]],
    info_window_screen_number: Optional[int],
) -> None:
    """
    Present SCENE(s), one at a time, in order.

    Each SCENE parameter must be the name of a Manim scene,
    with existing SCENE.json config file.

    You can present the same SCENE multiple times by repeating the parameter.

    Use ``manim-slide list-scenes`` to list all available
    scenes in a given folder.
    """
    if skip_all:
        exit_after_last_slide = True

    presentation_configs = get_scenes_presentation_config(scenes, folder)

    if config_path.exists():
        try:
            config = Config.from_file(config_path)
        except ValidationError as e:
            raise click.UsageError(str(e)) from None
    else:
        logger.debug("No configuration file found, using default configuration.")
        config = Config()

    if start_at[0]:
        start_at_scene_number = start_at[0]

    if start_at[1]:
        start_at_slide_number = start_at[1]

    from qtpy.QtCore import Qt
    from qtpy.QtGui import QScreen

    from ..qt_utils import qapp
    from .player import Player

    app = qapp()
    app.setApplicationName("Manim Slides")

    screens = app.screens()

    def get_screen(number: int) -> Optional[QScreen]:
        try:
            return screens[number]
        except IndexError:
            logger.error(
                f"Invalid screen number {number}, "
                f"allowed values are from 0 to {len(screens) - 1} (incl.)"
            )
            return None

    should_hide_info_window = False

    if hide_info_window is None:
        should_hide_info_window = len(screens) == 1
    elif hide_info_window == "always":
        should_hide_info_window = True

    if should_hide_info_window and info_window_screen_number is not None:
        logger.warning(
            f"Ignoring `--info-window-screen` because `--hide-info-window` is set to `{hide_info_window}`."
        )

    if screen_number is not None:
        screen = get_screen(screen_number)
    else:
        screen = None

    if info_window_screen_number is not None and not should_hide_info_window:
        info_window_screen = get_screen(info_window_screen_number)
    else:
        info_window_screen = None

    aspect_ratio_modes = {
        "keep": Qt.KeepAspectRatio,
        "ignore": Qt.IgnoreAspectRatio,
    }

    player = Player(
        config,
        presentation_configs,
        start_paused=start_paused,
        full_screen=full_screen,
        skip_all=skip_all,
        exit_after_last_slide=exit_after_last_slide,
        hide_mouse=hide_mouse,
        aspect_ratio_mode=aspect_ratio_modes[aspect_ratio],
        presentation_index=start_at_scene_number,
        slide_index=start_at_slide_number,
        screen=screen,
        playback_rate=playback_rate,
        next_terminates_loop=next_terminates_loop,
        hide_info_window=should_hide_info_window,
        info_window_screen=info_window_screen,
    )

    player.show(screens)

    signal.signal(signal.SIGINT, signal.SIG_DFL)
    sys.exit(app.exec())
