import math
import os
import platform
import sys
import time
from enum import IntEnum, auto, unique
from typing import List, Optional, Tuple

import click
import cv2
import numpy as np
from pydantic import ValidationError
from PyQt5 import QtGui
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from tqdm import tqdm

from .commons import config_path_option, verbosity_option
from .config import Config, PresentationConfig, SlideConfig, SlideType
from .defaults import FOLDER_PATH
from .manim import logger

os.environ.pop(
    "QT_QPA_PLATFORM_PLUGIN_PATH"
)  # See why here: https://stackoverflow.com/a/67863156

INTERPOLATION_FLAGS = {
    "nearest": cv2.INTER_NEAREST,
    "linear": cv2.INTER_LINEAR,
    "cubic": cv2.INTER_CUBIC,
    "area": cv2.INTER_AREA,
    "lanczos4": cv2.INTER_LANCZOS4,
    "linear-exact": cv2.INTER_LINEAR_EXACT,
    "nearest-exact": cv2.INTER_NEAREST_EXACT,
}

WINDOW_NAME = "Manim Slides"
WINDOW_INFO_NAME = f"{WINDOW_NAME}: Info"
WINDOWS = platform.system() == "Windows"


@unique
class State(IntEnum):
    """Represents all possible states of a slide presentation."""

    PLAYING = auto()
    PAUSED = auto()
    WAIT = auto()
    END = auto()

    def __str__(self) -> str:
        return self.name.capitalize()


def now() -> int:
    """Returns time.time() in milliseconds."""
    return round(time.time() * 1000)


def fix_time(t: float) -> float:
    """Clips time t such that it is always positive."""
    return t if t > 0 else 1


class Presentation:
    """Creates presentation from a configuration object."""

    def __init__(self, config: PresentationConfig) -> None:
        self.slides: List[SlideConfig] = config.slides
        self.files: List[str] = config.files

        self.current_slide_index: int = 0
        self.current_animation: int = self.current_slide.start_animation
        self.current_file: Optional[str] = None

        self.loaded_animation_cap: int = -1
        self.cap = None  # cap = cv2.VideoCapture

        self.reverse: bool = False
        self.reversed_animation: int = -1

        self.lastframe: Optional[np.ndarray] = None

        self.reset()
        self.add_last_slide()

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
        if self.reverse:
            self.current_animation = self.current_slide.end_animation - 1
        else:
            self.current_animation = self.current_slide.start_animation

        # self.current_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    def cancel_reverse(self) -> None:
        """Cancels any effet produced by a reversed slide."""
        if self.reverse:
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
        return max(
            self.current_cap.get(cv2.CAP_PROP_FPS), 1
        )  # TODO: understand why we sometimes get 0 fps

    def add_last_slide(self) -> None:
        """Add a 'last' slide to the end of slides."""
        self.slides.append(
            SlideConfig(
                start_animation=self.last_slide.end_animation,
                end_animation=self.last_slide.end_animation + 1,
                type=SlideType.last,
                number=self.last_slide.number + 1,
            )
        )

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

    def update_state(self, state) -> Tuple[np.ndarray, State]:
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
        elif state in [state.WAIT, state.PAUSED]:
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
                # self.current_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

        return self.lastframe, state


class Display(QThread):
    """Displays one or more presentations one after each other."""

    change_video_signal = pyqtSignal(np.ndarray)
    change_info_signal = pyqtSignal(dict)

    def __init__(
        self,
        presentations,
        config,
        start_paused=False,
        fullscreen=False,
        skip_all=False,
        resolution=(1980, 1080),
        interpolation_flag=cv2.INTER_LINEAR,
        record_to=None,
    ) -> None:
        super().__init__()
        self.presentations = presentations
        self.start_paused = start_paused
        self.config = config
        self.skip_all = skip_all
        self.fullscreen = fullscreen
        self.resolution = resolution
        self.interpolation_flag = interpolation_flag
        self.record_to = record_to
        self.recordings = []

        self.state = State.PLAYING
        self.lastframe: Optional[np.ndarray] = None
        self.current_presentation_index = 0
        self.run_flag = True

        self.lag = 0
        self.last_time = now()

    @property
    def current_presentation(self) -> Presentation:
        """Returns the current presentation."""
        return self.presentations[self.current_presentation_index]

    def run(self) -> None:
        """Runs a series of presentations until end or exit."""
        while self.run_flag:
            self.lastframe, self.state = self.current_presentation.update_state(
                self.state
            )
            if self.state == State.PLAYING or self.state == State.PAUSED:
                if self.start_paused:
                    self.state = State.PAUSED
                    self.start_paused = False
            if self.state == State.END:
                if self.current_presentation_index == len(self.presentations) - 1:
                    self.run_flag = False
                    continue
                else:
                    self.current_presentation_index += 1
                    self.state = State.PLAYING
            if not self.run_flag:
                continue
            self.show_video()

            self.lag = now() - self.last_time
            self.last_time = now()

            sleep_time = 1 / self.current_presentation.fps
            time.sleep(max(sleep_time - self.lag, 0))  # self.show_info()

        self.current_presentation.release_cap()

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
        info = np.zeros((130, 420), np.uint8)
        font_args = (FONT_ARGS[0], 0.7, *FONT_ARGS[2:])
        grid_x = [30, 230]
        grid_y = [30, 70, 110]

        cv2.putText(
            info,
            f"Animation: {self.current_presentation.current_animation}",
            (grid_x[0], grid_y[0]),
            *font_args,
        )
        cv2.putText(info, f"State: {self.state}", (grid_x[1], grid_y[0]), *font_args)

        cv2.putText(
            info,
            f"Slide {self.current_presentation.current_slide.number}/{len(self.current_presentation.slides)}",
            (grid_x[0], grid_y[1]),
            *font_args,
        )
        cv2.putText(
            info,
            f"Slide Type: {self.current_presentation.current_slide.type}",
            (grid_x[1], grid_y[1]),
            *font_args,
        )

        cv2.putText(
            info,
            f"Scene  {self.current_presentation_index + 1}/{len(self.presentations)}",
            ((grid_x[0] + grid_x[1]) // 2, grid_y[2]),
            *font_args,
        )

        # cv2.imshow(WINDOW_INFO_NAME, info)
        self.change_info_signal.emit({"prout": "ok"})

    def handle_key(self, key) -> None:
        """Handles key strokes."""

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

    def quit(self) -> None:
        """Destroys all windows created by presentations and exits gracefully."""
        self.exit = True

    def stop(self):
        self.run_flag = True
        self.wait()


class App(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__()
        # self.showFullScreen()
        self.setWindowTitle(WINDOW_NAME)
        self.display_width = 640
        self.display_height = 480

        self.setCursor(Qt.BlankCursor)
        self.label = QLabel(self)
        self.label.resize(self.display_width, self.display_height)

        self.pixmap = QPixmap(self.width(), self.height())
        self.label.setPixmap(self.pixmap)
        self.label.setMinimumSize(1, 1)

        # create the video capture thread
        self.thread = Display(*args, **kwargs)
        # connect its signal to the update_image slot
        self.thread.change_video_signal.connect(self.update_image)
        self.thread.change_info_signal.connect(self.update_info)
        # start the thread
        self.thread.start()

    def keyPressEvent(self, event):
        self.thread.handle_key(event.key())
        event.accept()

    def resizeEvent(self, event):
        self.pixmap = self.pixmap.scaled(self.width(), self.height())
        self.label.setPixmap(self.pixmap)
        self.label.resize(self.width(), self.height())

    def closeEvent(self, event):
        self.thread.stop()
        event.accept()

    # @pyqtSlot(List[Tuple[str, int, int]])
    def recordMovie(self, recordings: List[Tuple[str, int, int]]) -> None:
        logger.debug(
            f"A total of {len(self.recordings)} frames will be saved to {self.record_to}"
        )
        file, frame_number, fps = recordings[0]

        cap = cv2.VideoCapture(file)
        # cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number - 1)
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

    @pyqtSlot(np.ndarray)
    def update_image(self, cv_img: dict):
        """Updates the image_label with a new opencv image"""
        self.pixmap = self.convert_cv_qt(cv_img)
        self.label.setPixmap(self.pixmap)

    @pyqtSlot(dict)
    def update_info(self, info: dict):
        """Updates the image_label with a new opencv image"""
        pass

    def convert_cv_qt(self, cv_img):
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(
            rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888
        )
        p = convert_to_Qt_format.scaled(
            self.width(), self.height(), Qt.IgnoreAspectRatio
        )
        return QPixmap.fromImage(p)


@click.command()
@click.option(
    "--folder",
    default=FOLDER_PATH,
    type=click.Path(exists=True, file_okay=False),
    help="Set slides folder.",
    show_default=True,
)
@click.help_option("-h", "--help")
@verbosity_option
def list_scenes(folder) -> None:
    """List available scenes."""

    for i, scene in enumerate(_list_scenes(folder), start=1):
        click.secho(f"{i}: {scene}", fg="green")


def _list_scenes(folder) -> List[str]:
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

    logger.info(f"Found {len(scenes)} valid scene configuration files in `{folder}`.")

    return scenes


@click.command()
@click.argument("scenes", nargs=-1)
@config_path_option
@click.option(
    "--folder",
    default=FOLDER_PATH,
    type=click.Path(exists=True, file_okay=False),
    help="Set slides folder.",
    show_default=True,
)
@click.option("--start-paused", is_flag=True, help="Start paused.")
@click.option("--fullscreen", is_flag=True, help="Fullscreen mode.")
@click.option(
    "--skip-all",
    is_flag=True,
    help="Skip all slides, useful the test if slides are working.",
)
@click.option(
    "-r",
    "--resolution",
    type=(int, int),
    default=(1920, 1080),
    help="Window resolution WIDTH HEIGHT used if fullscreen is not set. You may manually resize the window afterward.",
    show_default=True,
)
@click.option(
    "-i",
    "--interpolation-flag",
    type=click.Choice(INTERPOLATION_FLAGS.keys(), case_sensitive=False),
    default="linear",
    help="Set the interpolation flag to be used when resizing image. See OpenCV cv::InterpolationFlags.",
    show_default=True,
)
@click.option(
    "--record-to",
    type=click.Path(dir_okay=False),
    default=None,
    help="If set, the presentation will be recorded into a AVI video file with given name.",
)
@click.help_option("-h", "--help")
@verbosity_option
def present(
    scenes,
    config_path,
    folder,
    start_paused,
    fullscreen,
    skip_all,
    resolution,
    interpolation_flag,
    record_to,
) -> None:
    """
    Present SCENE(s), one at a time, in order.

    Each SCENE parameter must be the name of a Manim scene, with existing SCENE.json config file.

    You can present the same SCENE multiple times by repeating the parameter.

    Use `manim-slide list-scenes` to list all available scenes in a given folder.
    """

    if len(scenes) == 0:
        scene_choices = _list_scenes(folder)

        scene_choices = dict(enumerate(scene_choices, start=1))

        for i, scene in scene_choices.items():
            click.secho(f"{i}: {scene}", fg="green")

        click.echo()

        click.echo("Choose number corresponding to desired scene/arguments.")
        click.echo("(Use comma separated list for multiple entries)")

        def value_proc(value: str) -> List[str]:
            indices = list(map(int, value.strip().replace(" ", "").split(",")))

            if not all(0 < i <= len(scene_choices) for i in indices):
                raise click.UsageError(
                    "Please only enter numbers displayed on the screen."
                )

            return [scene_choices[i] for i in indices]

        if len(scene_choices) == 0:
            raise click.UsageError(
                "No scenes were found, are you in the correct directory?"
            )

        while True:
            try:
                scenes = click.prompt("Choice(s)", value_proc=value_proc)
                break
            except ValueError as e:
                raise click.UsageError(e)

    presentations = []
    for scene in scenes:
        config_file = os.path.join(folder, f"{scene}.json")
        if not os.path.exists(config_file):
            raise click.UsageError(
                f"File {config_file} does not exist, check the scene name and make sure to use Slide as your scene base class"
            )
        try:
            pres_config = PresentationConfig.parse_file(config_file)
            presentations.append(Presentation(pres_config))
        except ValidationError as e:
            raise click.UsageError(str(e))

    if os.path.exists(config_path):
        try:
            config = Config.parse_file(config_path)
        except ValidationError as e:
            raise click.UsageError(str(e))
    else:
        logger.info("No configuration file found, using default configuration.")
        config = Config()

    if record_to is not None:
        _, ext = os.path.splitext(record_to)
        if ext.lower() != ".avi":
            raise click.UsageError(
                "Recording only support '.avi' extension. For other video formats, please convert the resulting '.avi' file afterwards."
            )

    app = QApplication(sys.argv)
    a = App(
        presentations,
        config=config,
        start_paused=start_paused,
        fullscreen=fullscreen,
        skip_all=skip_all,
        resolution=resolution,
        interpolation_flag=INTERPOLATION_FLAGS[interpolation_flag],
        record_to=record_to,
    )
    a.show()
    sys.exit(app.exec_())
    a.run()
