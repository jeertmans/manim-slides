from pathlib import Path
from typing import Any, List, Optional, Tuple

from manim import ThreeDScene, Scene, config

from .base import Base
from ..defaults import FFMPEG_BIN


class Slide(Base, Scene):
    """
    Inherits from :class:`Scene<manim.scene.scene.Scene>` and provide necessary tools for slides rendering.
    """
    @property
    def _ffmpeg_bin(self) -> Path:
        # Prior to v0.16.0.post0,
        # ffmpeg was stored as a constant in manim.constants
        try:
            return Path(config.ffmpeg_executable)
        except AttributeError:
            return FFMPEG_BIN

    @property
    def _frame_height(self) -> float:
        return config["frame_height"]  # type: ignore

    @property
    def _frame_width(self) -> float:
        return config["frame_width"]  # type: ignore

    @property
    def _background_color(self) -> str:
        color = config["background_color"]
        if hex_color := getattr(color, "hex", None):
            return hex_color  # type: ignore
        else:  # manim>=0.18, see https://github.com/ManimCommunity/manim/pull/3020
            return color.to_hex()  # type: ignore

    @property
    def _resolution(self) -> Tuple[int, int]:
        return config["pixel_width"], config["pixel_height"]

    @property
    def _partial_movie_files(self) -> List[Path]:
        return [Path(file) for file in self.renderer.file_writer.partial_movie_files]

    @property
    def _show_progress_bar(self) -> bool:
        return config["progress_bar"] != "none"  # type: ignore

    @property
    def _leave_progress_bar(self) -> bool:
        return config["progress_bar"] == "leave"  # type: ignore

    @property
    def _start_at_animation_number(self) -> Optional[int]:
        return config["from_animation_number"]  # type: ignore

    def render(self, *args: Any, **kwargs: Any) -> None:
        """MANIM render"""
        # We need to disable the caching limit since we rely on intermediate files
        max_files_cached = config["max_files_cached"]
        config["max_files_cached"] = float("inf")

        super().render(*args, **kwargs)

        config["max_files_cached"] = max_files_cached

        self._save_slides()


class ThreeDSlide(Slide, ThreeDScene):  # type: ignore
    """
    Inherits from :class:`Slide` and :class:`ThreeDScene<manim.scene.three_d_scene.ThreeDScene>` and provide necessary tools for slides rendering.

    .. note:: ManimGL does not need ThreeDScene for 3D rendering in recent versions, see `example.py`.

    Examples
    --------

    .. manim-slides:: ThreeDExample

        from manim import *
        from manim_slides import ThreeDSlide

        class ThreeDExample(ThreeDSlide):
            def construct(self):
                title = Text("A 2D Text")

                self.play(FadeIn(title))
                self.next_slide()

                sphere = Sphere([0, 0, -3])

                self.move_camera(phi=PI/3, theta=-PI/4, distance=7)
                self.play(
                    GrowFromCenter(sphere),
                    Transform(title, Text("A 3D Text"))
                )
                self.next_slide()

                bye = Text("Bye!")

                self.start_loop()
                self.play(
                    self.wipe(
                        self.mobjects_without_canvas,
                        [bye],
                        direction=UP
                    )
                )
                self.wait(.5)
                self.play(
                    self.wipe(
                        self.mobjects_without_canvas,
                        [title, sphere],
                        direction=DOWN
                    )
                )
                self.wait(.5)
                self.end_loop()

                self.play(*[FadeOut(mobject) for mobject in self.mobjects])
    """

    pass
