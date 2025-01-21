from pathlib import Path
from typing import Any, Optional

from manim import Scene, ThreeDScene, config
from manim.renderer.opengl_renderer import OpenGLRenderer
from manim.utils.color import rgba_to_color

from ..config import BaseSlideConfig
from .base import BaseSlide


class Slide(BaseSlide, Scene):  # type: ignore[misc]
    """
    Inherits from :class:`Scene<manim.scene.scene.Scene>` and provide necessary tools
    for slides rendering.

    :param args: Positional arguments passed to scene object.
    :param output_folder: Where the slide animation files should be written.
    :param kwargs: Keyword arguments passed to scene object.
    :cvar bool disable_caching: :data:`False`: Whether to disable the use of
        cached animation files.
    :cvar bool flush_cache: :data:`False`: Whether to flush the cache.

        Unlike with Manim, flushing is performed before rendering.
    :cvar bool skip_reversing: :data:`False`: Whether to generate reversed animations.

        If set to :data:`False`, and no cached reversed animation
        exists (or caching is disabled) for a given slide,
        then the reversed animation will be simply the same
        as the original one, i.e., ``rev_file = file``,
        for the current slide config.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # OpenGL renderer disables 'write_to_movie' by default
        # which is required for saving the animations
        config["write_to_movie"] = True
        super().__init__(*args, **kwargs)

    @property
    def _frame_shape(self) -> tuple[float, float]:
        if isinstance(self.renderer, OpenGLRenderer):
            return self.renderer.camera.frame_shape  # type: ignore
        else:
            return (
                self.renderer.camera.frame_height,
                self.renderer.camera.frame_width,
            )

    @property
    def _frame_height(self) -> float:
        return self._frame_shape[0]

    @property
    def _frame_width(self) -> float:
        return self._frame_shape[1]

    @property
    def _background_color(self) -> str:
        if isinstance(self.renderer, OpenGLRenderer):
            return rgba_to_color(self.renderer.background_color).to_hex()  # type: ignore
        else:
            return self.renderer.camera.background_color.to_hex()  # type: ignore

    @property
    def _resolution(self) -> tuple[int, int]:
        if isinstance(self.renderer, OpenGLRenderer):
            return self.renderer.get_pixel_shape()  # type: ignore
        else:
            return (
                self.renderer.camera.pixel_width,
                self.renderer.camera.pixel_height,
            )

    @property
    def _partial_movie_files(self) -> list[Path]:
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

    def play(self, *args: Any, **kwargs: Any) -> None:
        """Overload 'self.play' and increment animation count."""
        super().play(*args, **kwargs)

        if self._base_slide_config.skip_animations:
            # Manim will not render the animations, so we reset the animation
            # counter to the previous value
            self._current_animation -= 1

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
        Scene.next_section(
            self, *args, skip_animations=base_slide_config.skip_animations, **kwargs
        )
        BaseSlide.next_slide.__wrapped__(
            self,
            base_slide_config=base_slide_config,
        )

    def render(self, *args: Any, **kwargs: Any) -> None:
        """MANIM renderer."""
        # We need to disable the caching limit since we rely on intermediate files
        max_files_cached = config["max_files_cached"]
        config["max_files_cached"] = float("inf")

        flush_manim_cache = config["flush_cache"]

        if flush_manim_cache:
            # We need to postpone flushing *after* we saved slides
            config["flush_cache"] = False

        super().render(*args, **kwargs)

        config["max_files_cached"] = max_files_cached

        self._save_slides(
            use_cache=not (config["disable_caching"] or self.disable_caching),
            flush_cache=(config["flush_cache"] or self.flush_cache),
            skip_reversing=self.skip_reversing,
        )

        if flush_manim_cache:
            self.renderer.file_writer.flush_cache_directory()


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
