from pathlib import Path
from typing import Any, List, Optional, Tuple

from manim import Scene, ThreeDScene, config

from ..config import BaseSlideConfig
from .base import BaseSlide


class Slide(BaseSlide, Scene):  # type: ignore[misc]
    """
    Inherits from :class:`Scene<manim.scene.scene.Scene>` and provide necessary tools
    for slides rendering.
    """

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
        # When rendering with -na,b (manim only)
        # the animations not in [a,b] will be skipped,
        # but animation before a will have a None source file.
        return [
            Path(file)
            for file in self.renderer.file_writer.partial_movie_files
            if file is not None
        ]

    @property
    def _show_progress_bar(self) -> bool:
        return config["progress_bar"] != "none"  # type: ignore

    @property
    def _leave_progress_bar(self) -> bool:
        return config["progress_bar"] == "leave"  # type: ignore

    @property
    def _start_at_animation_number(self) -> Optional[int]:
        return config["from_animation_number"]  # type: ignore

    def next_section(self, *args: Any, **kwargs: Any) -> None:
        """
        Alias to :meth:`next_slide`.

        :param args:
            Positional arguments to be passed to :meth:`next_slide`.
        :param kwargs:
            Keyword arguments to be passed to :meth:`next_slide`.

        .. attention::

            This method is only available when using ``manim`` API.
        """
        self.next_slide(*args, **kwargs)

    @BaseSlideConfig.wrapper("base_slide_config")
    def next_slide(
        self,
        *args: Any,
        base_slide_config: BaseSlideConfig,
        **kwargs: Any,
    ) -> None:
        Scene.next_section(self, *args, **kwargs)
        BaseSlide.next_slide.__wrapped__(
            self,
            base_slide_config=base_slide_config,
        )

    def render(self, *args: Any, **kwargs: Any) -> None:
        """MANIM render."""
        # We need to disable the caching limit since we rely on intermediate files
        max_files_cached = config["max_files_cached"]
        config["max_files_cached"] = float("inf")

        super().render(*args, **kwargs)

        config["max_files_cached"] = max_files_cached

        self._save_slides()


class ThreeDSlide(Slide, ThreeDScene):  # type: ignore[misc]
    """
    Inherits from :class:`Slide` and
    :class:`ThreeDScene<manim.scene.three_d_scene.ThreeDScene>` and provide necessary
    tools for slides rendering.

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

                self.next_slide(loop=True)
                self.wipe(
                    self.mobjects_without_canvas,
                    [bye],
                    direction=UP
                )
                self.wait(.5)
                self.wipe(
                    self.mobjects_without_canvas,
                    [title, sphere],
                    direction=DOWN
                )
                self.wait(.5)
                self.next_slide()

                self.play(*[FadeOut(mobject) for mobject in self.mobjects])
    """

    pass
