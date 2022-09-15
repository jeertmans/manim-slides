import json
import math
import os
import platform
import sys
import time
from enum import IntEnum, auto, unique
from typing import List, Tuple

if platform.system() == "Windows":
    import ctypes

import click
import cv2
import numpy as np
from pydantic import ValidationError

from .commons import config_path_option
from .config import Config, PresentationConfig, SlideConfig, SlideType
from .defaults import CONFIG_PATH, FOLDER_PATH

WINDOW_NAME = "Manim Slides"


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
    """Returns time.time() in seconds."""
    return round(time.time() * 1000)


def fix_time(t: float) -> float:
    """Clips time t such that it is always positive."""
    return t if t > 0 else 1


class Presentation:
    """Creates presentation from a configuration object."""

    def __init__(self, config: PresentationConfig):
        self.slides: List[SlideConfig] = config.slides
        self.files: List[str] = config.files

        self.current_slide_index = 0
        self.current_animation = self.current_slide.start_animation

        self.loaded_animation_cap = -1
        self.cap = None  # cap = cv2.VideoCapture

        self.reverse = False
        self.reversed_animation = -1

        self.lastframe = None

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

    def release_cap(self):
        """Releases current Video Capture, if existing."""
        if not self.cap is None:
            self.cap.release()

        self.loaded_animation_cap = -1

    def load_animation_cap(self, animation: int):
        """Loads video file of given animation."""
        # We must load a new VideoCapture file if:
        if (self.loaded_animation_cap != animation) or (
            self.reverse and self.reversed_animation != animation
        ):  # cap already loaded

            self.release_cap()

            file = self.files[animation]

            if self.reverse:
                file = "{}_reversed{}".format(*os.path.splitext(file))
                self.reversed_animation = animation

            self.cap = cv2.VideoCapture(file)
            self.loaded_animation_cap = animation

    @property
    def current_cap(self) -> cv2.VideoCapture:
        """Returns current VideoCapture object."""
        self.load_animation_cap(self.current_animation)
        return self.cap

    def rewind_current_slide(self):
        """Rewinds current slide to first frame."""
        if self.reverse:
            self.current_animation = self.current_slide.end_animation - 1
        else:
            self.current_animation = self.current_slide.start_animation

        self.current_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    def reverse_current_slide(self):
        """Reverses current slide."""
        self.reverse = True
        self.rewind_current_slide()

    def load_next_slide(self):
        """Loads next slide."""
        if self.reverse:
            self.reverse = False
            self.reversed_animation = -1
            self.release_cap()
            self.rewind_current_slide()
        elif self.current_slide.is_last():
            self.current_slide.terminated = True
        else:
            self.current_slide_index = min(
                len(self.slides) - 1, self.current_slide_index + 1
            )
            self.rewind_current_slide()

    def load_previous_slide(self):
        """Loads previous slide."""
        self.current_slide_index = max(0, self.current_slide_index - 1)
        self.rewind_current_slide()

    @property
    def fps(self) -> int:
        """Returns the number of frames per second of the current video."""
        return self.current_cap.get(cv2.CAP_PROP_FPS)

    def add_last_slide(self):
        """Add a 'last' slide to the end of slides."""
        self.slides.append(
            SlideConfig(
                start_animation=self.last_slide.end_animation,
                end_animation=self.last_slide.end_animation + 1,
                type=SlideType.last,
                number=self.last_slide.number + 1,
            )
        )

    def reset(self):
        """Rests current presentation."""
        self.current_animation = 0
        self.load_animation_cap(0)
        self.current_slide_index = 0
        self.slides[-1].terminated = False

    def load_last_slide(self):
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
                print("HERE")
                state = State.WAIT
            else:
                # Play next video!
                self.current_animation = self.next_animation
                self.load_animation_cap(self.current_animation)
                # Reset video to position zero if it has been played before
                self.current_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

        return self.lastframe, state


class Display:
    """Displays one or more presentations one after each other."""

    def __init__(
        self,
        presentations,
        config,
        start_paused=False,
        fullscreen=False,
        skip_all=False,
    ):
        self.presentations = presentations
        self.start_paused = start_paused
        self.config = config
        self.skip_all = skip_all
        self.fullscreen = fullscreen
        self.is_windows = platform.system() == "Windows"

        self.state = State.PLAYING
        self.lastframe = None
        self.current_presentation_index = 0
        self.exit = False

        self.lag = 0
        self.last_time = now()

        if self.is_windows:
            user32 = ctypes.windll.user32
            self.screen_width, self.screen_height = user32.GetSystemMetrics(
                0
            ), user32.GetSystemMetrics(1)

        if self.fullscreen:
            cv2.namedWindow(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN)
            cv2.setWindowProperty(
                WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN
            )

    def resize_frame_to_screen(self, frame: np.ndarray):
        """
        Resizes a given frame to match screen dimensions.

        Only works on Windows.
        """
        assert self.is_windows, "Only Windows platforms need this method"
        frame_height, frame_width = frame.shape[:2]

        scale_height = self.screen_height / frame_height
        scale_width = self.screen_width / frame_width

        scale = min(scale_height, scale_width)

        return cv2.resize(frame, (int(scale * frame_height), int(scale * frame_width)))

    @property
    def current_presentation(self) -> Presentation:
        """Returns the current presentation"""
        return self.presentations[self.current_presentation_index]

    def run(self):
        """Runs a series of presentations until end or exit."""
        while not self.exit:
            self.lastframe, self.state = self.current_presentation.update_state(
                self.state
            )
            if self.state == State.PLAYING or self.state == State.PAUSED:
                if self.start_paused:
                    self.state = State.PAUSED
                    self.start_paused = False
            if self.state == State.END:
                if self.current_presentation_index == len(self.presentations) - 1:
                    self.quit()
                    continue
                else:
                    self.current_presentation_index += 1
                    self.state = State.PLAYING
            self.handle_key()
            self.show_video()
            self.show_info()

    def show_video(self):
        """Shows updated video."""
        self.lag = now() - self.last_time
        self.last_time = now()

        frame = self.lastframe

        if self.is_windows and self.fullscreen:
            frame = self.resize_frame_to_screen(frame)

        cv2.imshow(WINDOW_NAME, frame)

    def show_info(self):
        """Shows updated information about presentations."""
        info = np.zeros((130, 420), np.uint8)
        font_args = (cv2.FONT_HERSHEY_SIMPLEX, 0.7, 255)
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

        cv2.imshow(f"{WINDOW_NAME}: Info", info)

    def handle_key(self):
        """Handles key strokes."""
        sleep_time = math.ceil(1000 / self.current_presentation.fps)
        key = cv2.waitKeyEx(fix_time(sleep_time - self.lag))

        if self.config.QUIT.match(key):
            self.quit()
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
                    self.current_presentation.rewind_current_slide()
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
            self.current_presentation.rewind_current_slide()
            self.state = State.PLAYING

    def quit(self):
        """Destroys all windows created by presentations and exits gracefully."""
        cv2.destroyAllWindows()
        self.exit = True


@click.command()
@click.option(
    "--folder",
    default=FOLDER_PATH,
    type=click.Path(exists=True, file_okay=False),
    help="Set slides folder.",
)
@click.help_option("-h", "--help")
def list_scenes(folder):
    """List available scenes."""

    for i, scene in enumerate(_list_scenes(folder), start=1):
        click.secho(f"{i}: {scene}", fg="green")


def _list_scenes(folder) -> List[str]:
    """Lists available scenes in given directory."""
    scenes = []

    for file in os.listdir(folder):
        if file.endswith(".json"):
            try:
                filepath = os.path.join(folder, file)
                _ = PresentationConfig.parse_file(filepath)
                scenes.append(os.path.basename(file)[:-5])
            except Exception as e:  # Could not parse this file as a proper presentation config
                pass

    return scenes


@click.command()
@click.argument("scenes", nargs=-1)
@config_path_option
@click.option(
    "--folder",
    default=FOLDER_PATH,
    type=click.Path(exists=True, file_okay=False),
    help="Set slides folder.",
)
@click.option("--start-paused", is_flag=True, help="Start paused.")
@click.option("--fullscreen", is_flag=True, help="Fullscreen mode.")
@click.option(
    "--skip-all",
    is_flag=True,
    help="Skip all slides, useful the test if slides are working.",
)
@click.help_option("-h", "--help")
def present(scenes, config_path, folder, start_paused, fullscreen, skip_all):
    """Present the different scenes."""

    if len(scenes) == 0:
        scene_choices = _list_scenes(folder)

        scene_choices = dict(enumerate(scene_choices, start=1))

        for i, scene in scene_choices.items():
            click.secho(f"{i}: {scene}", fg="green")

        click.echo()

        click.echo("Choose number corresponding to desired scene/arguments.")
        click.echo("(Use comma separated list for multiple entries)")

        def value_proc(value: str):
            indices = list(map(int, value.strip().replace(" ", "").split(",")))

            if not all(map(lambda i: 0 < i <= len(scene_choices), indices)):
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

    presentations = list()
    for scene in scenes:
        config_file = os.path.join(folder, f"{scene}.json")
        if not os.path.exists(config_file):
            raise click.UsageError(
                f"File {config_file} does not exist, check the scene name and make sure to use Slide as your scene base class"
            )
        try:
            config = PresentationConfig.parse_file(config_file)
            presentations.append(Presentation(config))
        except ValidationError as e:
            raise click.UsageError(str(e))

    if os.path.exists(config_path):
        try:
            config = Config.parse_file(config_path)
        except ValidationError as e:
            raise click.UsageError(str(e))
    else:
        config = Config()

    display = Display(
        presentations,
        config=config,
        start_paused=start_paused,
        fullscreen=fullscreen,
        skip_all=skip_all,
    )
    display.run()
