import signal
import sys
from pathlib import Path
from typing import Optional

import click
from click import Context, Parameter
from pydantic import ValidationError

from ...core.config import Config, PresentationConfig, list_presentation_configs
from ...core.logger import logger
from ..commons import (
    config_path_option,
    folder_path_option,
    scenes_argument,
    verbosity_option,
)

PREFERRED_QT_VERSIONS = ("6.5.1", "6.5.2")


def warn_if_non_desirable_pyside6_version() -> None:
    from qtpy import API, QT_VERSION

    if sys.version_info < (3, 12) and (
        API != "pyside6" or QT_VERSION not in PREFERRED_QT_VERSIONS
    ):
        logger.warn(
            f"You are using {API = }, {QT_VERSION = }, "
            "but we recommend installing 'PySide6==6.5.2', mainly to avoid "
            "flashing screens between slides, "
            "see issue https://github.com/jeertmans/manim-slides/issues/293. "
            "You can do so with `pip install 'manim-slides[pyside6]'`."
        )


@click.command()
@folder_path_option
@click.help_option("-h", "--help")
@verbosity_option
def list_scenes(folder: Path) -> None:
    """List available scenes."""
    scene_names = [path.stem for path in list_presentation_configs(folder)]
    num_digits = len(str(len(scene_names)))
    for i, scene_name in enumerate(scene_names, start=1):
        click.secho(f"{i:{num_digits}d}: {scene_name}", fg="green")


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
@scenes_argument
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
    is_flag=True,
    help="Hide info window.",
)
@click.option(
    "--info-window-screen",
    "info_window_screen_number",
    metavar="NUMBER",
    type=int,
    default=None,
    help="Put info window on the given screen (a.k.a. display).",
)
@click.help_option("-h", "--help")
@verbosity_option
def present(
    scenes: list[Path],
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
    hide_info_window: bool,
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

    presentation_configs = [PresentationConfig.from_file(path) for path in scenes]

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

    warn_if_non_desirable_pyside6_version()

    from qtpy.QtCore import Qt
    from qtpy.QtGui import QScreen

    from ..qt_utils import qapp
    from .player import Player

    app = qapp()
    app.setApplicationName("Manim Slides")

    def get_screen(number: int) -> Optional[QScreen]:
        try:
            return app.screens()[number]
        except IndexError:
            logger.error(
                f"Invalid screen number {number}, "
                f"allowed values are from 0 to {len(app.screens())-1} (incl.)"
            )
            return None

    if screen_number is not None:
        screen = get_screen(screen_number)
    else:
        screen = None

    if info_window_screen_number is not None:
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
        hide_info_window=hide_info_window,
        info_window_screen=info_window_screen,
    )

    player.show()

    signal.signal(signal.SIGINT, signal.SIG_DFL)
    sys.exit(app.exec())
