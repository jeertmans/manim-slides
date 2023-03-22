import os
import platform
import shutil
import subprocess
from typing import Any, List, Optional, Tuple
from warnings import warn

from tqdm import tqdm

from .config import PresentationConfig, SlideConfig, SlideType
from .defaults import FOLDER_PATH
from .manim import FFMPEG_BIN, MANIMGL, Scene, ThreeDScene, config, logger


def reverse_video_file(src: str, dst: str) -> None:
    """Reverses a video file, writting the result to `dst`."""
    command = [FFMPEG_BIN, "-i", src, "-vf", "reverse", dst]
    logger.debug(" ".join(command))
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = process.communicate()

    if output:
        logger.debug(output.decode())

    if error:
        logger.debug(error.decode())


class Slide(Scene):  # type:ignore
    """
    Inherits from :class:`manim.scene.scene.Scene` or :class:`manimlib.scene.scene.Scene` and provide necessary tools for slides rendering.
    """

    def __init__(
        self, *args: Any, output_folder: str = FOLDER_PATH, **kwargs: Any
    ) -> None:
        if MANIMGL:
            if not os.path.isdir("videos"):
                os.mkdir("videos")
            kwargs["file_writer_config"] = {
                "break_into_partial_movies": True,
                "output_directory": "",
                "write_to_movie": True,
            }

            kwargs["preview"] = False

        super().__init__(*args, **kwargs)

        self.__output_folder = output_folder
        self.__slides: List[SlideConfig] = []
        self.__current_slide = 1
        self.__current_animation = 0
        self.__loop_start_animation: Optional[int] = None
        self.__pause_start_animation = 0

    @property
    def __background_color(self) -> str:
        """Returns the scene's background color."""
        if MANIMGL:
            return self.camera_config["background_color"].hex  # type: ignore
        else:
            return config["background_color"].hex  # type: ignore

    @property
    def __resolution(self) -> Tuple[int, int]:
        """Returns the scene's resolution used during rendering."""
        if MANIMGL:
            return self.camera_config["pixel_width"], self.camera_config["pixel_height"]
        else:
            return config["pixel_width"], config["pixel_height"]

    @property
    def __partial_movie_files(self) -> List[str]:
        """Returns a list of partial movie files, a.k.a animations."""
        if MANIMGL:
            from manimlib.utils.file_ops import get_sorted_integer_files

            kwargs = {
                "remove_non_integer_files": True,
                "extension": self.file_writer.movie_file_extension,
            }
            return get_sorted_integer_files(  # type: ignore
                self.file_writer.partial_movie_directory, **kwargs
            )
        else:
            return self.renderer.file_writer.partial_movie_files  # type: ignore

    @property
    def __show_progress_bar(self) -> bool:
        """Returns True if progress bar should be displayed."""
        if MANIMGL:
            return getattr(self, "show_progress_bar", True)
        else:
            return config["progress_bar"] != "none"  # type: ignore

    @property
    def __leave_progress_bar(self) -> bool:
        """Returns True if progress bar should be left after completed."""
        if MANIMGL:
            return getattr(self, "leave_progress_bars", False)
        else:
            return config["progress_bar"] == "leave"  # type: ignore

    @property
    def __start_at_animation_number(self) -> Optional[int]:
        if MANIMGL:
            return getattr(self, "start_at_animation_number", None)
        else:
            return config["from_animation_number"]  # type: ignore

    def play(self, *args: Any, **kwargs: Any) -> None:
        """Overloads `self.play` and increment animation count."""
        super().play(*args, **kwargs)
        self.__current_animation += 1

    def next_slide(self) -> None:
        """
        Creates a new slide with previous animations.

        This usually means that the user will need to press some key before the
        next slide is played. By default, this is the right arrow key.


        .. note::

            Calls to :func:`next_slide` at the very beginning or at the end are
            not needed, since they are automatically added.

        .. warning::

            This is not allowed to call :func:`next_slide` inside a loop.

        Examples
        --------

        The following contains 3 slides:

        #. the first with nothing on it;
        #. the second with "Hello World!" fading in;
        #. and the last with the text fading out;

        .. code-block:: python

            from manim import *
            from manim_slides import Slide

            class Example(Slide):
                def construct(self):
                    text = Text("Hello World!")

                    self.next_slide()
                    self.play(FadeIn(text))

                    self.next_slide()
                    self.play(FadeOut(text))
        """
        assert (
            self.__loop_start_animation is None
        ), "You cannot call `self.next_slide()` inside a loop"

        self.__slides.append(
            SlideConfig(
                type=SlideType.slide,
                start_animation=self.__pause_start_animation,
                end_animation=self.__current_animation,
                number=self.__current_slide,
            )
        )
        self.__current_slide += 1
        self.__pause_start_animation = self.__current_animation

    def pause(self) -> None:
        """
        Creates a new slide with previous animations.

        .. deprecated:: 4.10.0
            Use :func:`next_slide` instead.
        """
        warn(
            "`self.pause()` is deprecated. Use `self.next_slide()` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        Slide.next_slide(self)

    def __add_last_slide(self) -> None:
        """Adds a 'last' slide to the end of slides."""

        if (
            len(self.__slides) > 0
            and self.__current_animation == self.__slides[-1].end_animation
        ):
            self.__slides[-1].type = SlideType.last
            return

        self.__slides.append(
            SlideConfig(
                type=SlideType.last,
                start_animation=self.__pause_start_animation,
                end_animation=self.__current_animation,
                number=self.__current_slide,
            )
        )

    def start_loop(self) -> None:
        """
        Starts a loop. End it with :func:`end_loop`.

        A loop will automatically replay the slide, i.e., everything between
        :func:`start_loop` and :func:`end_loop`, upon reaching end.

        Examples
        --------

        The following contains one slide that will loop endlessly.

        .. code-block:: python

            from manim import *
            from manim_slides import Slide

            class Example(Slide):
                def construct(self):
                    dot = Dot(color=BLUE)

                    self.start_loop()

                    self.play(Indicate(dot))

                    self.end_loop()
        """
        assert self.__loop_start_animation is None, "You cannot nest loops"
        self.__loop_start_animation = self.__current_animation

    def end_loop(self) -> None:
        """Ends an existing loop. See :func:`start_loop` for more details."""
        assert (
            self.__loop_start_animation is not None
        ), "You have to start a loop before ending it"
        self.__slides.append(
            SlideConfig(
                type=SlideType.loop,
                start_animation=self.__loop_start_animation,
                end_animation=self.__current_animation,
                number=self.__current_slide,
            )
        )
        self.__current_slide += 1
        self.__loop_start_animation = None
        self.__pause_start_animation = self.__current_animation

    def __save_slides(self, use_cache: bool = True) -> None:
        """
        Saves slides, optionally using cached files.

        Note that cached files only work with Manim.
        """
        self.__add_last_slide()

        if not os.path.exists(self.__output_folder):
            os.mkdir(self.__output_folder)

        files_folder = os.path.join(self.__output_folder, "files")
        if not os.path.exists(files_folder):
            os.mkdir(files_folder)

        scene_name = str(self)
        scene_files_folder = os.path.join(files_folder, scene_name)

        old_animation_files = set()

        if not os.path.exists(scene_files_folder):
            os.mkdir(scene_files_folder)
        elif not use_cache:
            shutil.rmtree(scene_files_folder)
            os.mkdir(scene_files_folder)
        else:
            old_animation_files.update(os.listdir(scene_files_folder))

        files = []
        for src_file in tqdm(
            self.__partial_movie_files,
            desc=f"Copying animation files to '{scene_files_folder}' and generating reversed animations",
            leave=self.__leave_progress_bar,
            ascii=True if platform.system() == "Windows" else None,
            disable=not self.__show_progress_bar,
        ):
            if src_file is None and not MANIMGL:
                # This happens if rendering with -na,b (manim only)
                # where animations not in [a,b] will be skipped
                # but animations before a will have a None src_file
                continue

            filename = os.path.basename(src_file)
            rev_filename = "{}_reversed{}".format(*os.path.splitext(filename))

            dst_file = os.path.join(scene_files_folder, filename)
            # We only copy animation if it was not present
            if filename in old_animation_files:
                old_animation_files.remove(filename)
            else:
                shutil.copyfile(src_file, dst_file)

            # We only reverse video if it was not present
            if rev_filename in old_animation_files:
                old_animation_files.remove(rev_filename)
            else:
                rev_file = os.path.join(scene_files_folder, rev_filename)
                reverse_video_file(src_file, rev_file)

            files.append(dst_file)

        if offset := self.__start_at_animation_number:
            self.__slides = [
                slide for slide in self.__slides if slide.end_animation > offset
            ]

            for slide in self.__slides:
                slide.start_animation -= offset
                slide.end_animation -= offset

        logger.info(
            f"Copied {len(files)} animations to '{os.path.abspath(scene_files_folder)}' and generated reversed animations"
        )

        slide_path = os.path.join(self.__output_folder, "%s.json" % (scene_name,))

        with open(slide_path, "w") as f:
            f.write(
                PresentationConfig(
                    slides=self.__slides,
                    files=files,
                    resolution=self.__resolution,
                    background_color=self.__background_color,
                ).json(indent=2)
            )

        logger.info(
            f"Slide '{scene_name}' configuration written in '{os.path.abspath(slide_path)}'"
        )

    def run(self, *args: Any, **kwargs: Any) -> None:
        """MANIMGL renderer"""
        super().run(*args, **kwargs)
        self.__save_slides(use_cache=False)

    def render(self, *args: Any, **kwargs: Any) -> None:
        """MANIM render"""
        # We need to disable the caching limit since we rely on intermediate files
        max_files_cached = config["max_files_cached"]
        config["max_files_cached"] = float("inf")

        super().render(*args, **kwargs)

        config["max_files_cached"] = max_files_cached

        self.__save_slides()


class ThreeDSlide(Slide, ThreeDScene):  # type: ignore
    """
    Inherits from :class:`Slide` and :class:`manim.scene.three_d_scene.ThreeDScene` or :class:`manimlib.scene.three_d_scene.ThreeDScene` and provide necessary tools for slides rendering.

    .. note:: ManimGL does not need ThreeDScene for 3D rendering in recent versions, see `example.py`.
    """

    pass
