import os
import platform
import sys
import time
from enum import IntEnum, auto, unique
from typing import Any, Dict, List, Optional, Tuple, Union

import click
import cv2
import numpy as np
from pydantic import ValidationError
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QCloseEvent, QIcon, QImage, QKeyEvent, QPixmap, QResizeEvent
from PySide6.QtWidgets import QApplication, QGridLayout, QLabel, QWidget
from tqdm import tqdm

from .commons import config_path_option, verbosity_option
from .config import DEFAULT_CONFIG, Config, PresentationConfig, SlideConfig
from .defaults import FOLDER_PATH
from .manim import logger
from .resources import *  # noqa: F401, F403

os.environ.pop(
    "QT_QPA_PLATFORM_PLUGIN_PATH", None
)  # See why here: https://stackoverflow.com/a/67863156

WINDOW_NAME = "Manim Slides"
WINDOW_INFO_NAME = f"{WINDOW_NAME}: Info"
WINDOWS = platform.system() == "Windows"

ASPECT_RATIO_MODES = {
    "ignore": Qt.IgnoreAspectRatio,
    "keep": Qt.KeepAspectRatio,
}

RESIZE_MODES = {
    "fast": Qt.FastTransformation,
    "smooth": Qt.SmoothTransformation,
}


@unique
class State(IntEnum):
    """Represents all possible states of a slide presentation."""

    PLAYING = auto()
    PAUSED = auto()
    WAIT = auto()
    END = auto()

    def __str__(self) -> str:
        return self.name.capitalize()


def now() -> float:
    """Returns time.time() in seconds."""
    return time.time()


class Presentation:
    """Creates presentation from a configuration object."""

    def __init__(self, config: PresentationConfig) -> None:
        self.slides: List[SlideConfig] = config.slides
        self.files: List[str] = config.files

        self.current_slide_index: int = 0
        self.current_animation: int = self.current_slide.start_animation
        self.current_file: str = ""

        self.loaded_animation_cap: int = -1
        self.cap = None  # cap = cv2.VideoCapture

        self.reverse: bool = False
        self.reversed_animation: int = -1

        self.lastframe: Optional[np.ndarray] = None

        self.reset()

    @property
    def current_slide(self) -> SlideConfig:
        """Returns currently playing slide."""
        return self.slides[self.current_slide_index]

    @property
    def first_slide(self) -> SlideConfig:
        """Returns first slide."""
        return self.slides[0]

    @property
    def last_slide(self) -> SlideConfig:
        """Returns last slide."""
        return self.slides[-1]

    def release_cap(self) -> None:
        """Releases current Video Capture, if existing."""
        if self.cap is not None:
            self.cap.release()

        self.loaded_animation_cap = -1

    def load_animation_cap(self, animation: int) -> None:
        """Loads video file of given animation."""
        # We must load a new VideoCapture file if:
        if (self.loaded_animation_cap != animation) or (
            self.reverse and self.reversed_animation != animation
        ):  # cap already loaded

            logger.debug(f"Loading new cap for animation #{animation}")

            self.release_cap()

            file: str = self.files[animation]

            if self.reverse:
                file = "{}_reversed{}".format(*os.path.splitext(file))
                self.reversed_animation = animation

            self.current_file = file

            self.cap = cv2.VideoCapture(file)
            self.loaded_animation_cap = animation

    @property
    def current_cap(self) -> cv2.VideoCapture:
        """Returns current VideoCapture object."""
        self.load_animation_cap(self.current_animation)
        return self.cap

    def rewind_current_slide(self) -> None:
        """Rewinds current slide to first frame."""
        logger.debug("Rewinding curring slide")
        if self.reverse:
            self.current_animation = self.current_slide.end_animation - 1
        else:
            self.current_animation = self.current_slide.start_animation

        cap = self.current_cap
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    def cancel_reverse(self) -> None:
        """Cancels any effet produced by a reversed slide."""
        if self.reverse:
            logger.debug("Cancelling effects from previous 'reverse' action'")
            self.reverse = False
            self.reversed_animation = -1
            self.release_cap()

    def reverse_current_slide(self) -> None:
        """Reverses current slide."""
        self.reverse = True
        self.rewind_current_slide()

    def load_next_slide(self) -> None:
        """Loads next slide."""
        logger.debug("Loading next slide")
        if self.reverse:
            self.cancel_reverse()
            self.rewind_current_slide()
        elif self.current_slide.is_last():
            self.current_slide.terminated = True
        else:
            self.current_slide_index = min(
                len(self.slides) - 1, self.current_slide_index + 1
            )
            self.rewind_current_slide()

    def load_previous_slide(self) -> None:
        """Loads previous slide."""
        logger.debug("Loading previous slide")
        self.cancel_reverse()
        self.current_slide_index = max(0, self.current_slide_index - 1)
        self.rewind_current_slide()

    @property
    def fps(self) -> int:
        """Returns the number of frames per second of the current video."""
        fps = self.current_cap.get(cv2.CAP_PROP_FPS)
        if fps == 0:
            logger.warn(
                f"Something is wrong with video file {self.current_file}, as the fps returned by frame {self.current_frame_number} is 0"
            )
        return max(fps, 1)  # TODO: understand why we sometimes get 0 fps

    def reset(self) -> None:
        """Rests current presentation."""
        self.current_animation = 0
        self.load_animation_cap(0)
        self.current_slide_index = 0
        self.slides[-1].terminated = False

    def load_last_slide(self) -> None:
        """Loads last slide."""
        self.current_slide_index = len(self.slides) - 2
        assert (
            self.current_slide_index >= 0
        ), "Slides should be at list of a least two elements"
        self.current_animation = self.current_slide.start_animation
        self.load_animation_cap(self.current_animation)
        self.slides[-1].terminated = False

    @property
    def next_animation(self) -> int:
        """Returns the next animation."""
        if self.reverse:
            return self.current_animation - 1
        else:
            return self.current_animation + 1

    @property
    def is_last_animation(self) -> int:
        """Returns True if current animation is the last one of current slide."""
        if self.reverse:
            return self.current_animation == self.current_slide.start_animation
        else:
            return self.next_animation == self.current_slide.end_animation

    @property
    def current_frame_number(self) -> int:
        """Returns current frame number."""
        return int(self.current_cap.get(cv2.CAP_PROP_POS_FRAMES))

    def update_state(self, state: State) -> Tuple[np.ndarray, State]:
        """
        Updates the current state given the previous one.

        It does this by reading the video information and checking if the state is still correct.
        It returns the frame to show (lastframe) and the new state.
        """
        if state == State.PAUSED:
            if self.lastframe is None:
                _, self.lastframe = self.current_cap.read()
            return self.lastframe, state
        still_playing, frame = self.current_cap.read()
        if still_playing:
            self.lastframe = frame
        elif state == state.WAIT or state == state.PAUSED:  # type: ignore
            return self.lastframe, state
        elif self.current_slide.is_last() and self.current_slide.terminated:
            return self.lastframe, State.END
        else:  # not still playing
            if self.is_last_animation:
                if self.current_slide.is_slide():
                    state = State.WAIT
                elif self.current_slide.is_loop():
                    if self.reverse:
                        state = State.WAIT
                    else:
                        self.current_animation = self.current_slide.start_animation
                        state = State.PLAYING
                        self.rewind_current_slide()
                elif self.current_slide.is_last():
                    self.current_slide.terminated = True
            elif (
                self.current_slide.is_last()
                and self.current_slide.end_animation == self.current_animation
            ):
                state = State.WAIT
            else:
                # Play next video!
                self.current_animation = self.next_animation
                self.load_animation_cap(self.current_animation)
                # Reset video to position zero if it has been played before
                self.current_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

        return self.lastframe, state


class Display(QThread):  # type: ignore
    """Displays one or more presentations one after each other."""

    change_video_signal = Signal(np.ndarray)
    change_info_signal = Signal(dict)
    finished = Signal()

    def __init__(
        self,
        presentations: List[PresentationConfig],
        config: Config = DEFAULT_CONFIG,
        start_paused: bool = False,
        skip_all: bool = False,
        record_to: Optional[str] = None,
        exit_after_last_slide: bool = False,
    ) -> None:
        super().__init__()
        self.presentations = presentations
        self.start_paused = start_paused
        self.config = config
        self.skip_all = skip_all
        self.record_to = record_to
        self.recordings: List[Tuple[str, int, int]] = []

        self.state = State.PLAYING
        self.lastframe: Optional[np.ndarray] = None
        self.current_presentation_index = 0
        self.run_flag = True

        self.key = -1
        self.exit_after_last_slide = exit_after_last_slide

    @property
    def current_presentation(self) -> Presentation:
        """Returns the current presentation."""
        return self.presentations[self.current_presentation_index]

    def run(self) -> None:
        """Runs a series of presentations until end or exit."""
        while self.run_flag:
            last_time = now()
            self.lastframe, self.state = self.current_presentation.update_state(
                self.state
            )
            if self.state == State.PLAYING or self.state == State.PAUSED:
                if self.start_paused:
                    self.state = State.PAUSED
                    self.start_paused = False
            if self.state == State.END:
                if self.current_presentation_index == len(self.presentations) - 1:
                    if self.exit_after_last_slide:
                        self.run_flag = False
                        continue
                else:
                    self.current_presentation_index += 1
                    self.state = State.PLAYING

            self.handle_key()
            self.show_video()
            self.show_info()

            lag = now() - last_time
            sleep_time = 1 / self.current_presentation.fps
            sleep_time = max(sleep_time - lag, 0)
            time.sleep(sleep_time)
            last_time = now()
        self.current_presentation.release_cap()

        if self.record_to is not None:
            self.record_movie()

        logger.debug("Closing video thread gracully and exiting")
        self.finished.emit()

    def record_movie(self) -> None:
        logger.debug(
            f"A total of {len(self.recordings)} frames will be saved to {self.record_to}"
        )
        file, frame_number, fps = self.recordings[0]

        cap = cv2.VideoCapture(file)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number - 1)
        _, frame = cap.read()

        w, h = frame.shape[:2]
        fourcc = cv2.VideoWriter_fourcc(*"XVID")
        out = cv2.VideoWriter(self.record_to, fourcc, fps, (h, w))

        out.write(frame)

        for _file, frame_number, _ in tqdm(
            self.recordings[1:], desc="Creating recording file", leave=False
        ):
            if file != _file:
                cap.release()
                file = _file
                cap = cv2.VideoCapture(_file)

            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number - 1)
            _, frame = cap.read()
            out.write(frame)

        cap.release()
        out.release()

    def show_video(self) -> None:
        """Shows updated video."""
        if self.record_to is not None:
            pres = self.current_presentation
            self.recordings.append(
                (pres.current_file, pres.current_frame_number, pres.fps)
            )

        frame: np.ndarray = self.lastframe
        self.change_video_signal.emit(frame)

    def show_info(self) -> None:
        """Shows updated information about presentations."""
        self.change_info_signal.emit(
            {
                "animation": self.current_presentation.current_animation,
                "state": self.state,
                "slide_index": self.current_presentation.current_slide.number,
                "n_slides": len(self.current_presentation.slides),
                "type": self.current_presentation.current_slide.type,
                "scene_index": self.current_presentation_index + 1,
                "n_scenes": len(self.presentations),
            }
        )

    @Slot(int)
    def set_key(self, key: int) -> None:
        """Sets the next key to be handled."""
        self.key = key

    def handle_key(self) -> None:
        """Handles key strokes."""

        key = self.key

        if self.config.QUIT.match(key):
            self.run_flag = False
        elif self.state == State.PLAYING and self.config.PLAY_PAUSE.match(key):
            self.state = State.PAUSED
        elif self.state == State.PAUSED and self.config.PLAY_PAUSE.match(key):
            self.state = State.PLAYING
        elif self.state == State.WAIT and (
            self.config.CONTINUE.match(key) or self.config.PLAY_PAUSE.match(key)
        ):
            self.current_presentation.load_next_slide()
            self.state = State.PLAYING
        elif (
            self.state == State.PLAYING and self.config.CONTINUE.match(key)
        ) or self.skip_all:
            self.current_presentation.load_next_slide()
        elif self.config.BACK.match(key):
            if self.current_presentation.current_slide_index == 0:
                if self.current_presentation_index == 0:
                    self.current_presentation.load_previous_slide()
                else:
                    self.current_presentation_index -= 1
                    self.current_presentation.load_last_slide()
                self.state = State.PLAYING
            else:
                self.current_presentation.load_previous_slide()
                self.state = State.PLAYING
        elif self.config.REVERSE.match(key):
            self.current_presentation.reverse_current_slide()
            self.state = State.PLAYING
        elif self.config.REWIND.match(key):
            self.current_presentation.cancel_reverse()
            self.current_presentation.rewind_current_slide()
            self.state = State.PLAYING

        self.key = -1  # No more key to be handled

    def stop(self) -> None:
        """Stops current thread, without doing anything after."""
        self.run_flag = False
        self.wait()


class Info(QWidget):  # type: ignore
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(WINDOW_INFO_NAME)

        self.layout = QGridLayout()

        self.setLayout(self.layout)

        self.animationLabel = QLabel()
        self.stateLabel = QLabel()
        self.slideLabel = QLabel()
        self.typeLabel = QLabel()
        self.sceneLabel = QLabel()

        self.layout.addWidget(self.animationLabel, 0, 0, 1, 2)
        self.layout.addWidget(self.stateLabel, 1, 0)
        self.layout.addWidget(self.slideLabel, 1, 1)
        self.layout.addWidget(self.typeLabel, 2, 0)
        self.layout.addWidget(self.sceneLabel, 2, 1)

        self.update_info({})

    @Slot(dict)
    def update_info(self, info: Dict[str, Union[str, int]]) -> None:
        self.animationLabel.setText("Animation: {}".format(info.get("animation", "na")))
        self.stateLabel.setText("State: {}".format(info.get("state", "unknown")))
        self.slideLabel.setText(
            "Slide: {}/{}".format(
                info.get("slide_index", "na"), info.get("n_slides", "na")
            )
        )
        self.typeLabel.setText("Slide Type: {}".format(info.get("type", "unknown")))
        self.sceneLabel.setText(
            "Scene: {}/{}".format(
                info.get("scene_index", "na"), info.get("n_scenes", "na")
            )
        )


class InfoThread(QThread):  # type: ignore
    def __init__(self) -> None:
        super().__init__()
        self.dialog = Info()
        self.run_flag = True

    def start(self) -> None:
        super().start()

        self.dialog.show()

    def stop(self) -> None:
        self.dialog.deleteLater()


class App(QWidget):  # type: ignore
    send_key_signal = Signal(int)

    def __init__(
        self,
        *args: Any,
        config: Config = DEFAULT_CONFIG,
        fullscreen: bool = False,
        resolution: Tuple[int, int] = (1980, 1080),
        hide_mouse: bool = False,
        aspect_ratio: Qt.AspectRatioMode = Qt.IgnoreAspectRatio,
        resize_mode: Qt.TransformationMode = Qt.SmoothTransformation,
        background_color: str = "black",
        **kwargs: Any,
    ):
        super().__init__()

        self.setWindowTitle(WINDOW_NAME)
        self.icon = QIcon(":/icon.png")
        self.setWindowIcon(self.icon)
        self.display_width, self.display_height = resolution
        self.aspect_ratio = aspect_ratio
        self.resize_mode = resize_mode
        self.hide_mouse = hide_mouse
        self.config = config
        if self.hide_mouse:
            self.setCursor(Qt.BlankCursor)

        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.resize(self.display_width, self.display_height)
        self.label.setStyleSheet(f"background-color: {background_color}")

        self.pixmap = QPixmap(self.width(), self.height())
        self.label.setPixmap(self.pixmap)
        self.label.setMinimumSize(1, 1)

        # create the video capture thread
        kwargs["config"] = config
        self.thread = Display(*args, **kwargs)
        # create the info dialog
        self.info = Info()
        self.info.show()

        # info widget will also listen to key presses
        self.info.keyPressEvent = self.keyPressEvent

        if fullscreen:
            self.showFullScreen()

        # connect signals
        self.thread.change_video_signal.connect(self.update_image)
        self.thread.change_info_signal.connect(self.info.update_info)
        self.thread.finished.connect(self.closeAll)
        self.send_key_signal.connect(self.thread.set_key)

        # start the thread
        self.thread.start()

    def keyPressEvent(self, event: QKeyEvent) -> None:

        key = event.key()
        if self.config.HIDE_MOUSE.match(key):
            if self.hide_mouse:
                self.setCursor(Qt.ArrowCursor)
                self.hide_mouse = False
            else:
                self.setCursor(Qt.BlankCursor)
                self.hide_mouse = True
        # We send key to be handled by video display
        self.send_key_signal.emit(key)
        event.accept()

    def closeAll(self) -> None:
        logger.debug("Closing all QT windows")
        self.thread.stop()
        self.info.deleteLater()
        self.deleteLater()

    def resizeEvent(self, event: QResizeEvent) -> None:
        self.pixmap = self.pixmap.scaled(
            self.width(), self.height(), self.aspect_ratio, self.resize_mode
        )
        self.label.setPixmap(self.pixmap)
        self.label.resize(self.width(), self.height())

    def closeEvent(self, event: QCloseEvent) -> None:
        self.closeAll()
        event.accept()

    @Slot(np.ndarray)
    def update_image(self, cv_img: np.ndarray) -> None:
        """Updates the (image) label with a new opencv image"""
        h, w, ch = cv_img.shape
        bytes_per_line = ch * w
        qt_img = QImage(cv_img.data, w, h, bytes_per_line, QImage.Format_BGR888)

        if w != self.width() or h != self.height():
            qt_img = qt_img.scaled(
                self.width(), self.height(), self.aspect_ratio, self.resize_mode
            )

        self.label.setPixmap(QPixmap.fromImage(qt_img))


@click.command()
@click.option(
    "--folder",
    metavar="DIRECTORY",
    default=FOLDER_PATH,
    type=click.Path(exists=True, file_okay=False),
    help="Set slides folder.",
    show_default=True,
)
@click.help_option("-h", "--help")
@verbosity_option
def list_scenes(folder: str) -> None:
    """List available scenes."""

    for i, scene in enumerate(_list_scenes(folder), start=1):
        click.secho(f"{i}: {scene}", fg="green")


def _list_scenes(folder: str) -> List[str]:
    """Lists available scenes in given directory."""
    scenes = []

    for file in os.listdir(folder):
        if file.endswith(".json"):
            filepath = os.path.join(folder, file)
            try:
                _ = PresentationConfig.parse_file(filepath)
                scenes.append(os.path.basename(file)[:-5])
            except Exception as e:  # Could not parse this file as a proper presentation config
                logger.warn(
                    f"Something went wrong with parsing presentation config `{filepath}`: {e}"
                )
                pass

    logger.debug(f"Found {len(scenes)} valid scene configuration files in `{folder}`.")

    return scenes


def prompt_for_scenes(folder: str) -> List[str]:
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
            return scenes
        except ValueError as e:
            raise click.UsageError(str(e))


def get_scenes_presentation_config(
    scenes: List[str], folder: str
) -> List[PresentationConfig]:
    """Returns a list of presentation configurations based on the user input."""

    if len(scenes) == 0:
        scenes = prompt_for_scenes(folder)

    presentation_configs = []
    for scene in scenes:
        config_file = os.path.join(folder, f"{scene}.json")
        if not os.path.exists(config_file):
            raise click.UsageError(
                f"File {config_file} does not exist, check the scene name and make sure to use Slide as your scene base class"
            )
        try:
            presentation_configs.append(PresentationConfig.parse_file(config_file))
        except ValidationError as e:
            raise click.UsageError(str(e))

    return presentation_configs


@click.command()
@click.argument("scenes", nargs=-1)
@config_path_option
@click.option(
    "--folder",
    metavar="DIRECTORY",
    default=FOLDER_PATH,
    type=click.Path(exists=True, file_okay=False),
    help="Set slides folder.",
    show_default=True,
)
@click.option("--start-paused", is_flag=True, help="Start paused.")
@click.option("--fullscreen", is_flag=True, help="Fullscreen mode.")
@click.option(
    "-s",
    "--skip-all",
    is_flag=True,
    help="Skip all slides, useful the test if slides are working. Automatically sets `--skip-after-last-slide` to True.",
)
@click.option(
    "-r",
    "--resolution",
    metavar="<WIDTH HEIGHT>",
    type=(int, int),
    default=(1920, 1080),
    help="Window resolution WIDTH HEIGHT used if fullscreen is not set. You may manually resize the window afterward.",
    show_default=True,
)
@click.option(
    "--to",
    "--record-to",
    "record_to",
    metavar="FILE",
    type=click.Path(dir_okay=False),
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
    "--aspect-ratio",
    type=click.Choice(ASPECT_RATIO_MODES.keys(), case_sensitive=False),
    default="ignore",
    help="Set the aspect ratio mode to be used when rescaling video.",
    show_default=True,
)
@click.option(
    "--resize-mode",
    type=click.Choice(RESIZE_MODES.keys(), case_sensitive=False),
    default="smooth",
    help="Set the resize (i.e., transformation) mode to be used when rescaling video.",
    show_default=True,
)
@click.option(
    "--background-color",
    "--bgcolor",
    "background_color",
    metavar="COLOR",
    type=str,
    default="black",
    help='Set the background color for borders when using "keep" resize mode. Can be any valid CSS color, e.g., "green", "#FF6500" or "rgba(255, 255, 0, .5)".',
    show_default=True,
)
@click.help_option("-h", "--help")
@verbosity_option
def present(
    scenes: List[str],
    config_path: str,
    folder: str,
    start_paused: bool,
    fullscreen: bool,
    skip_all: bool,
    resolution: Tuple[int, int],
    record_to: Optional[str],
    exit_after_last_slide: bool,
    hide_mouse: bool,
    aspect_ratio: str,
    resize_mode: str,
    background_color: str,
) -> None:
    """
    Present SCENE(s), one at a time, in order.

    Each SCENE parameter must be the name of a Manim scene, with existing SCENE.json config file.

    You can present the same SCENE multiple times by repeating the parameter.

    Use `manim-slide list-scenes` to list all available scenes in a given folder.
    """

    if skip_all:
        exit_after_last_slide = True

    presentations = [
        Presentation(presentation_config)
        for presentation_config in get_scenes_presentation_config(scenes, folder)
    ]

    if os.path.exists(config_path):
        try:
            config = Config.parse_file(config_path)
        except ValidationError as e:
            raise click.UsageError(str(e))
    else:
        logger.debug("No configuration file found, using default configuration.")
        config = Config()

    if record_to is not None:
        _, ext = os.path.splitext(record_to)
        if ext.lower() != ".avi":
            raise click.UsageError(
                "Recording only support '.avi' extension. For other video formats, please convert the resulting '.avi' file afterwards."
            )

    app = QApplication(sys.argv)
    app.setApplicationName("Manim Slides")
    a = App(
        presentations,
        config=config,
        start_paused=start_paused,
        fullscreen=fullscreen,
        skip_all=skip_all,
        resolution=resolution,
        record_to=record_to,
        exit_after_last_slide=exit_after_last_slide,
        hide_mouse=hide_mouse,
        aspect_ratio=ASPECT_RATIO_MODES[aspect_ratio],
        resize_mode=RESIZE_MODES[resize_mode],
        background_color=background_color,
    )
    a.show()
    sys.exit(app.exec_())
    logger.debug("After")
