import signal
import sys
from pathlib import Path
from typing import List, Optional, Tuple

import click
from click import Context, Parameter
from pydantic import ValidationError
from PySide6.QtWidgets import QApplication

from ..commons import config_path_option, verbosity_option
from ..config import Config, PresentationConfig
from ..defaults import FOLDER_PATH
from ..logger import logger
from .player import VideoPlayer


@click.command()
@click.option(
    "--folder",
    metavar="DIRECTORY",
    default=FOLDER_PATH,
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Set slides folder.",
    show_default=True,
)
@click.help_option("-h", "--help")
@verbosity_option
def list_scenes(folder: Path) -> None:
    """List available scenes."""

    for i, scene in enumerate(_list_scenes(folder), start=1):
        click.secho(f"{i}: {scene}", fg="green")


def _list_scenes(folder: Path) -> List[str]:
    """Lists available scenes in given directory."""
    scenes = []

    for filepath in folder.glob("*.json"):
        try:
            _ = PresentationConfig.from_file(filepath)
            scenes.append(filepath.stem)
        except (
            Exception
        ) as e:  # Could not parse this file as a proper presentation config
            logger.warn(
                f"Something went wrong with parsing presentation config `{filepath}`: {e}"
            )
            pass

    logger.debug(f"Found {len(scenes)} valid scene configuration files in `{folder}`.")

    return scenes


def prompt_for_scenes(folder: Path) -> List[str]:
    """Prompts the user to select scenes within a given folder."""

    scene_choices = dict(enumerate(_list_scenes(folder), start=1))

    for i, scene in scene_choices.items():
        click.secho(f"{i}: {scene}", fg="green")

    click.echo()

    click.echo("Choose number corresponding to desired scene/arguments.")
    click.echo("(Use comma separated list for multiple entries)")

    def value_proc(value: Optional[str]) -> List[str]:
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
            raise click.UsageError(str(e))


def get_scenes_presentation_config(
    scenes: List[str], folder: Path
) -> List[PresentationConfig]:
    """Returns a list of presentation configurations based on the user input."""

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
            raise click.UsageError(str(e))

    return presentation_configs


def start_at_callback(
    ctx: Context, param: Parameter, values: str
) -> Tuple[Optional[int], ...]:
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
                )

    values_tuple = values.split(",")
    n_values = len(values_tuple)
    if n_values == 2:
        return tuple(map(str_to_int_or_none, values_tuple))

    raise click.BadParameter(
        f"exactly 2 arguments are expected but you gave {n_values}, please use commas to separate them",
        ctx=ctx,
        param=param,
    )


@click.command()
@click.argument("scenes", nargs=-1)
@config_path_option
@click.option(
    "--folder",
    metavar="DIRECTORY",
    default=FOLDER_PATH,
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Set slides folder.",
    show_default=True,
)
@click.option("--start-paused", is_flag=True, help="Start paused.")
@click.option("--fullscreen", is_flag=True, help="Fullscreen mode.")
@click.option(
    "-s",
    "--skip-all",
    is_flag=True,
    help="Skip all slides, useful the test if slides are working. Automatically sets `--exit-after-last-slide` to True.",
)
@click.option(
    "-r",
    "--resolution",
    metavar="<WIDTH HEIGHT>",
    type=(int, int),
    default=None,
    help="Window resolution WIDTH HEIGHT used if fullscreen is not set. You may manually resize the window afterward.",
)
@click.option(
    "--to",
    "--record-to",
    "record_to",
    metavar="FILE",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="If set, the presentation will be recorded into a AVI video file with given name.",
)
@click.option(
    "--exit-after-last-slide",
    is_flag=True,
    help="At the end of last slide, the application will be exited.",
)
@click.option(
    "--hide-mouse",
    is_flag=True,
    help="Hide mouse cursor.",
)
@click.option(
    "--background-color",
    "--bgcolor",
    "background_color",
    metavar="COLOR",
    type=str,
    default=None,
    help='Set the background color for borders when using "keep" resize mode. Can be any valid CSS color, e.g., "green", "#FF6500" or "rgba(255, 255, 0, .5)". If not set, it defaults to the background color configured in the Manim scene.',
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
    help="Start presenting at (x, y), equivalent to --sacn x --sasn y, and overrides values if not None.",
)
@click.option(
    "--sacn",
    "--start-at-scene-number",
    "start_at_scene_number",
    metavar="INDEX",
    type=int,
    default=None,
    help="Start presenting at a given scene number (0 is first, -1 is last).",
)
@click.option(
    "--sasn",
    "--start-at-slide-number",
    "start_at_slide_number",
    metavar="INDEX",
    type=int,
    default=None,
    help="Start presenting at a given slide number (0 is first, -1 is last).",
)
@click.option(
    "--screen",
    "screen_number",
    metavar="NUMBER",
    type=int,
    default=None,
    help="Presents content on the given screen (a.k.a. display).",
)
@click.help_option("-h", "--help")
@verbosity_option
def present(
    scenes: List[str],
    config_path: Path,
    folder: Path,
    start_paused: bool,
    fullscreen: bool,
    skip_all: bool,
    resolution: Optional[Tuple[int, int]],
    record_to: Optional[Path],
    exit_after_last_slide: bool,
    hide_mouse: bool,
    background_color: Optional[str],
    start_at: Tuple[Optional[int], Optional[int], Optional[int]],
    start_at_scene_number: Optional[int],
    start_at_slide_number: Optional[int],
    screen_number: Optional[int] = None,
) -> None:
    """
    Present SCENE(s), one at a time, in order.

    Each SCENE parameter must be the name of a Manim scene, with existing SCENE.json config file.

    You can present the same SCENE multiple times by repeating the parameter.

    Use `manim-slide list-scenes` to list all available scenes in a given folder.
    """

    if skip_all:
        exit_after_last_slide = True

    presentation_configs = get_scenes_presentation_config(scenes, folder)

    if resolution is not None:
        for presentation_config in presentation_configs:
            presentation_config.resolution = resolution

    if background_color is not None:
        for presentation_config in presentation_configs:
            presentation_config.background_color = background_color

    if config_path.exists():
        try:
            config = Config.from_file(config_path)
        except ValidationError as e:
            raise click.UsageError(str(e))
    else:
        logger.debug("No configuration file found, using default configuration.")
        config = Config()

    if record_to is not None:
        ext = record_to.suffix
        if ext.lower() != ".avi":
            raise click.UsageError(
                "Recording only support '.avi' extension. "
                "For other video formats, "
                "please convert the resulting '.avi' file afterwards."
            )

    if start_at[0]:
        start_at[0]

    if start_at[1]:
        start_at[1]

    if not QApplication.instance():
        app = QApplication(sys.argv)
    else:
        app = QApplication.instance()

    app.setApplicationName("Manim Slides")

    if screen_number is not None:
        try:
            app.screens()[screen_number]
        except IndexError:
            logger.error(
                f"Invalid screen number {screen_number}, "
                f"allowed values are from 0 to {len(app.screens())-1} (incl.)"
            )
    else:
        pass

    # a = App(
    #    presentations,
    #    config=config,
    #    start_paused=start_paused,
    #    fullscreen=fullscreen,
    #    skip_all=skip_all,
    #    record_to=record_to,
    #    exit_after_last_slide=exit_after_last_slide,
    #    hide_mouse=hide_mouse,
    #    aspect_ratio=ASPECT_RATIO_MODES[aspect_ratio],
    #    resize_mode=RESIZE_MODES[resize_mode],
    #    start_at_scene_number=start_at_scene_number,
    #    start_at_slide_number=start_at_slide_number,
    #    start_at_animation_number=start_at_animation_number,
    #    screen=screen,
    # )

    a = VideoPlayer(config, presentation_configs, exit_after_last_slide=exit_after_last_slide)

    a.show()

    # inform about CTRL+C
    def sigkill_handler(signum, frame):  # type: ignore
        logger.warn(
            "Thie application cannot be closed with usual CTRL+C, "
            "please use the appropriate key defined in your config "
            "(default: q)."
        )

        raise KeyboardInterrupt

    signal.signal(signal.SIGINT, sigkill_handler)
    sys.exit(app.exec_())
