import os
import platform
import shutil
import subprocess
from typing import Any, List, Optional

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
    Inherits from `manim.Scene` or `manimlib.Scene` and provide necessary tools for slides rendering.
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

        self.output_folder = output_folder
        self.slides: List[SlideConfig] = []
        self.current_slide = 1
        self.current_animation = 0
        self.loop_start_animation: Optional[int] = None
        self.pause_start_animation = 0

    @property
    def partial_movie_files(self) -> List[str]:
        """Returns a list of partial movie files, a.k.a animations."""
        if MANIMGL:
            from manimlib.utils.file_ops import get_sorted_integer_files

            kwargs = {
                "remove_non_integer_files": True,
                "extension": self.file_writer.movie_file_extension,
            }
            return get_sorted_integer_files(
                self.file_writer.partial_movie_directory, **kwargs
            )
        else:
            return self.renderer.file_writer.partial_movie_files

    @property
    def show_progress_bar(self) -> bool:
        """Returns True if progress bar should be displayed."""
        if MANIMGL:
            return getattr(super(Scene, self), "show_progress_bar", True)
        else:
            return config["progress_bar"] != "none"

    @property
    def leave_progress_bar(self) -> bool:
        """Returns True if progress bar should be left after completed."""
        if MANIMGL:
            return getattr(super(Scene, self), "leave_progress_bars", False)
        else:
            return config["progress_bar"] == "leave"

    def play(self, *args: Any, **kwargs: Any) -> None:
        """Overloads `self.play` and increment animation count."""
        super().play(*args, **kwargs)
        self.current_animation += 1

    def pause(self) -> None:
        """Creates a new slide with previous animations."""
        self.slides.append(
            SlideConfig(
                type=SlideType.slide,
                start_animation=self.pause_start_animation,
                end_animation=self.current_animation,
                number=self.current_slide,
            )
        )
        self.current_slide += 1
        self.pause_start_animation = self.current_animation

    def add_last_slide(self) -> None:
        """Adds a 'last' slide to the end of slides."""
        self.slides.append(
            SlideConfig(
                type=SlideType.last,
                start_animation=self.pause_start_animation,
                end_animation=self.current_animation,
                number=self.current_slide,
            )
        )

    def start_loop(self) -> None:
        """Starts a loop."""
        assert self.loop_start_animation is None, "You cannot nest loops"
        self.loop_start_animation = self.current_animation

    def end_loop(self) -> None:
        """Ends an existing loop."""
        assert (
            self.loop_start_animation is not None
        ), "You have to start a loop before ending it"
        self.slides.append(
            SlideConfig(
                type=SlideType.loop,
                start_animation=self.loop_start_animation,
                end_animation=self.current_animation,
                number=self.current_slide,
            )
        )
        self.current_slide += 1
        self.loop_start_animation = None
        self.pause_start_animation = self.current_animation

    def save_slides(self, use_cache: bool = True) -> None:
        """
        Saves slides, optionally using cached files.

        Note that cached files only work with Manim.
        """
        self.add_last_slide()

        if not os.path.exists(self.output_folder):
            os.mkdir(self.output_folder)

        files_folder = os.path.join(self.output_folder, "files")
        if not os.path.exists(files_folder):
            os.mkdir(files_folder)

        scene_name = type(self).__name__
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
            self.partial_movie_files,
            desc=f"Copying animation files to '{scene_files_folder}' and generating reversed animations",
            leave=self.leave_progress_bar,
            ascii=True if platform.system() == "Windows" else None,
            disable=not self.show_progress_bar,
        ):
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

        logger.info(
            f"Copied {len(files)} animations to '{os.path.abspath(scene_files_folder)}' and generated reversed animations"
        )

        slide_path = os.path.join(self.output_folder, "%s.json" % (scene_name,))

        with open(slide_path, "w") as f:
            f.write(PresentationConfig(slides=self.slides, files=files).json(indent=2))

        logger.info(
            f"Slide '{scene_name}' configuration written in '{os.path.abspath(slide_path)}'"
        )

    def run(self, *args: Any, **kwargs: Any) -> None:
        """MANIMGL renderer"""
        super().run(*args, **kwargs)
        self.save_slides(use_cache=False)

    def render(self, *args: Any, **kwargs: Any) -> None:
        """MANIM render"""
        # We need to disable the caching limit since we rely on intermidiate files
        max_files_cached = config["max_files_cached"]
        config["max_files_cached"] = float("inf")

        super().render(*args, **kwargs)

        config["max_files_cached"] = max_files_cached

        self.save_slides()


class ThreeDSlide(Slide, ThreeDScene):  # type: ignore
    """
    Inherits from `manim.ThreeDScene` or `manimlib.ThreeDScene` and provide necessary tools for slides rendering.

    Note that ManimGL does not need ThreeDScene for 3D rendering in recent versions, see `example.py`.
    """

    pass
