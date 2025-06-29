from __future__ import annotations

__all__ = ["BaseSlide"]

import json
import shutil
from abc import abstractmethod
from collections.abc import MutableMapping, Sequence, ValuesView
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
)

import numpy as np

from ..config import BaseSlideConfig, PreSlideConfig
from ..defaults import FOLDER_PATH
from ..utils import (
    process_static_image,
)
from . import MANIM

if TYPE_CHECKING:
    from .animation import Wipe, Zoom

if MANIM:
    from manim.mobject.mobject import Mobject
else:
    Mobject = Any

LEFT: np.ndarray = np.array([-1.0, 0.0, 0.0])


class BaseSlide:
    disable_caching: bool = False
    flush_cache: bool = False
    skip_reversing: bool = False
    max_duration_before_split_reverse: float | None = 4.0
    num_processes: int | None = None

    def __init__(
        self, *args: Any, output_folder: Path = FOLDER_PATH, **kwargs: Any
    ) -> None:
        super().__init__(*args, **kwargs)
        self._output_folder: Path = output_folder
        self._slides: list[PreSlideConfig] = []
        self._base_slide_config: BaseSlideConfig = BaseSlideConfig()
        self._current_slide = 1
        self._current_animation = 0
        self._start_animation = 0
        self._canvas: MutableMapping[str, Mobject] = {}
        self._wait_time_between_slides = 0.0
        self._skip_animations = False

    @property
    @abstractmethod
    def _frame_height(self) -> float:
        """Return the scene's frame height."""
        raise NotImplementedError

    @property
    @abstractmethod
    def _frame_width(self) -> float:
        """Return the scene's frame width."""
        raise NotImplementedError

    @property
    @abstractmethod
    def _background_color(self) -> str:
        """Return the scene's background color."""
        raise NotImplementedError

    @property
    @abstractmethod
    def _resolution(self) -> tuple[int, int]:
        """Return the scene's resolution used during rendering."""
        raise NotImplementedError

    @property
    @abstractmethod
    def _partial_movie_files(self) -> list[Path]:
        """Return a list of partial movie files, a.k.a animations."""
        raise NotImplementedError

    @property
    @abstractmethod
    def _show_progress_bar(self) -> bool:
        """Return True if progress bar should be displayed."""
        raise NotImplementedError

    @property
    @abstractmethod
    def _leave_progress_bar(self) -> bool:
        """Return True if progress bar should be left after completed."""
        raise NotImplementedError

    @property
    @abstractmethod
    def _start_at_animation_number(self) -> int | None:
        """If set, return the animation number at which rendering start."""
        raise NotImplementedError

    @property
    def canvas(self) -> MutableMapping[str, Mobject]:
        """
        Return the canvas associated to the current slide.

        The canvas is a mapping between names and Mobjects,
        for objects that are assumed to stay in multiple slides.

        For example, a section title or a slide number.

        Examples
        --------
        .. manim-slides:: CanvasExample

            from manim import *
            from manim_slides import Slide

            class CanvasExample(Slide):
                def update_canvas(self):
                    self.counter += 1
                    old_slide_number = self.canvas["slide_number"]
                    new_slide_number = Text(f"{self.counter}").move_to(old_slide_number)
                    self.play(Transform(old_slide_number, new_slide_number))

                def construct(self):
                    title = Text("My Title").to_corner(UL)

                    self.counter = 1
                    slide_number = Text("1").to_corner(DL)

                    self.add_to_canvas(title=title, slide_number=slide_number)

                    self.play(FadeIn(title), FadeIn(slide_number))
                    self.next_slide()

                    circle = Circle(radius=2)
                    dot = Dot()

                    self.update_canvas()
                    self.play(Create(circle))
                    self.play(MoveAlongPath(dot, circle))

                    self.next_slide()
                    self.update_canvas()

                    square = Square()

                    self.wipe(self.mobjects_without_canvas, square)
                    self.next_slide()

                    self.update_canvas()
                    self.play(
                        Transform(
                            self.canvas["title"],
                            Text("New Title").to_corner(UL)
                        )
                    )
                    self.next_slide()

                    self.remove_from_canvas("title", "slide_number")
                    self.wipe(self.mobjects_without_canvas, [])

        """
        return self._canvas

    def add_to_canvas(self, **objects: Mobject) -> None:
        """
        Add objects to the canvas, using key values as names.

        :param objects: A mapping between names and Mobjects.

        .. note::

            This method does not actually do anything in terms of
            animations. You must still call :code:`self.add` or
            play some animation that introduces each Mobject for
            it to appear. The same applies when removing objects.

        .. seealso::

            :attr:`canvas` for usage examples.
        """
        self._canvas.update(objects)

    def remove_from_canvas(self, *names: str) -> None:
        """
        Remove objects from the canvas.

        :param names: The names of objects to remove.

        .. seealso::

            :attr:`canvas` for usage examples.
        """
        for name in names:
            self._canvas.pop(name)

    @property
    def canvas_mobjects(self) -> ValuesView[Mobject]:
        """Return Mobjects contained in the canvas."""
        return self.canvas.values()

    @property
    def mobjects_without_canvas(self) -> Sequence[Mobject]:
        """
        Return the list of Mobjects contained in the scene, minus those present in
        the canvas.

        .. seealso::

            :attr:`canvas` for usage examples.
        """
        return [
            mobject
            for mobject in self.mobjects  # type: ignore[attr-defined]
            if mobject not in self.canvas_mobjects
        ]

    @property
    def wait_time_between_slides(self) -> float:
        r"""
        Return the wait duration (in seconds) added between two slides.

        By default, this value is set to 0.

        Setting this value to something bigger than 0 will result in a
        :code:`self.wait` animation called at the end of every slide.

        .. note::
            This is useful because animations are usually only terminated
            when a new animation is played. You can observe the small difference
            in the examples below: the circle is not fully complete in the first
            slide of the first example, but well in the second example.

        Examples
        --------
        .. manim-slides:: WithoutWaitExample

            from manim import *
            from manim_slides import Slide

            class WithoutWaitExample(Slide):
                def construct(self):
                    circle = Circle(radius=2)
                    arrow = Arrow().next_to(circle, RIGHT).scale(-1)
                    text = Text("Small\ngap").next_to(arrow, RIGHT)

                    self.play(Create(arrow), FadeIn(text))
                    self.play(Create(circle))
                    self.next_slide()

                    self.play(FadeOut(circle))

        .. manim-slides:: WithWaitExample

            from manim import *
            from manim_slides import Slide

            class WithWaitExample(Slide):
                def construct(self):
                    self.wait_time_between_slides = 0.1  # A small value > 1 / FPS
                    circle = Circle(radius=2)
                    arrow = Arrow().next_to(circle, RIGHT).scale(-1)
                    text = Text("No more\ngap").next_to(arrow, RIGHT)

                    self.play(Create(arrow), FadeIn(text))
                    self.play(Create(circle))
                    self.next_slide()

                    self.play(FadeOut(circle))

        """
        return self._wait_time_between_slides

    @wait_time_between_slides.setter
    def wait_time_between_slides(self, wait_time: float) -> None:
        self._wait_time_between_slides = max(wait_time, 0.0)

    def play(self, *args: Any, **kwargs: Any) -> None:
        """Overload 'self.play' and increment animation count."""
        super().play(*args, **kwargs)  # type: ignore[misc]
        self._current_animation += 1

    @BaseSlideConfig.wrapper("base_slide_config")
    def next_slide(
        self,
        *,
        base_slide_config: BaseSlideConfig,
        **kwargs: Any,
    ) -> None:
        """
        Create a new slide with previous animations, and setup options
        for the next slide.

        This usually means that the user will need to press some key before the
        next slide is played. By default, this is the right arrow key.

        :param args:
            Positional arguments passed to
            :meth:`Scene.next_section<manim.scene.scene.Scene.next_section>`,
            or ignored if `manimlib` API is used.
        :param skip_animations:
            Exclude the next slide from the output.

            If `manim` is used, this is also passed to :meth:`Scene.next_section<manim.scene.scene.Scene.next_section>`,
            which will avoid rendering the corresponding animations.

            .. seealso::

                :meth:`start_skip_animations`
                :meth:`stop_skip_animations`
        :param loop:
            If set, next slide will be looping.
        :param auto_next:
            If set, next slide will play immediately play the next slide
            upon terminating.

            .. warning::

                Only supported by ``manim-slides present``
                and ``manim-slides convert --to=html``.
        :param playback_rate:
            Playback rate at which the video is played.

            .. warning::

                Only supported by ``manim-slides present``.
        :param reversed_playback_rate:
            Playback rate at which the reversed video is played.

            .. warning::

                Only supported by ``manim-slides present``.
        :param notes:
            Presenter notes, in Markdown format.

            .. note::
                PowerPoint does not support Markdown formatting,
                so the text will be displayed as is.

            .. warning::

                Only supported by ``manim-slides present``,
                ``manim-slides convert --to=html`` and
                ``manim-slides convert --to=pptx``.
        :param dedent_notes:
            If set, apply :func:`textwrap.dedent` to notes.
        :param pathlib.Path src:
            An optional path to a video file to include as next slide.

            The video will be copied into the output folder, but no rescaling
            is applied.
        :param static_image:
            An optional path to an image file or PIL Image object to include as next slide.

            The image will be copied into the output folder, but no rescaling
            is applied.
        :param kwargs:
            Keyword arguments passed to
            :meth:`Scene.next_section<manim.scene.scene.Scene.next_section>`,
            or ignored if `manimlib` API is used.

        .. note::

            Calls to :func:`next_slide` at the very beginning or at the end are
            not needed, since they are automatically added.

        .. warning::

            When rendered with RevealJS, loops cannot be in the first nor
            the last slide.

        .. seealso::

            When using ``manim`` API, this method will also call
            :meth:`Scene.next_section<manim.scene.scene.Scene.next_section>`.

        Examples
        --------
        The following contains 3 slides:

        #. the first with nothing on it;
        #. the second with "Hello World!" fading in;
        #. and the last with the text fading out;

        .. manim-slides:: NextSlideExample

            from manim import *
            from manim_slides import Slide

            class NextSlideExample(Slide):
                def construct(self):
                    text = Text("Hello World!")

                    self.play(FadeIn(text))

                    self.next_slide()
                    self.play(FadeOut(text))

        The following contains one slide that will loop endlessly.

        .. manim-slides:: LoopExample

            from manim import *
            from manim_slides import Slide

            class LoopExample(Slide):
                def construct(self):
                    dot = Dot(color=BLUE, radius=1)

                    self.play(FadeIn(dot))

                    self.next_slide(loop=True)

                    self.play(Indicate(dot, scale_factor=2))

                    self.next_slide()

                    self.play(FadeOut(dot))

        The following contains one slide that triggers the next slide
        upon terminating.

        .. manim-slides:: AutoNextExample

            from manim import *
            from manim_slides import Slide

            class AutoNextExample(Slide):
                def construct(self):
                    square = Square(color=RED, side_length=2)

                    self.play(GrowFromCenter(square))

                    self.next_slide(auto_next=True)

                    self.play(Wiggle(square))

                    self.next_slide()

                    self.wipe(square)

        The following contains speaker notes. On the webbrowser,
        the speaker view can be triggered by pressing :kbd:`S`.

        .. manim-slides:: SpeakerNotesExample

            from manim import *
            from manim_slides import Slide

            class SpeakerNotesExample(Slide):
                def construct(self):
                    self.next_slide(notes="Some introduction")
                    square = Square(color=GREEN, side_length=2)

                    self.play(GrowFromCenter(square))

                    self.next_slide(notes="We now rotate the slide")

                    self.play(Rotate(square, PI / 2))

                    self.next_slide(notes="Bye bye")

                    self.zoom(square)

        """
        if self._current_animation > self._start_animation:
            if self.wait_time_between_slides > 0.0:
                self.wait(self.wait_time_between_slides)  # type: ignore[attr-defined]

            self._slides.append(
                PreSlideConfig.from_base_slide_config_and_animation_indices(
                    self._base_slide_config,
                    self._start_animation,
                    self._current_animation,
                )
            )

            self._current_slide += 1

        if base_slide_config.src is not None:
            self._slides.append(
                PreSlideConfig.from_base_slide_config_and_animation_indices(
                    base_slide_config,
                    self._current_animation,
                    self._current_animation,
                )
            )

            base_slide_config = BaseSlideConfig()  # default
            self._current_slide += 1

        if base_slide_config.static_image is not None:
            self._slides.append(
                PreSlideConfig.from_base_slide_config_and_animation_indices(
                    base_slide_config,
                    self._current_animation,
                    self._current_animation,
                )
            )

            base_slide_config = BaseSlideConfig()  # default
            self._current_slide += 1

        if self._skip_animations:
            base_slide_config.skip_animations = True

        self._base_slide_config = base_slide_config
        self._start_animation = self._current_animation

    def _add_last_slide(self) -> None:
        """Add a 'last' slide to the end of slides."""
        if (
            len(self._slides) > 0
            and self._current_animation == self._slides[-1].end_animation
        ):
            return

        self._slides.append(
            PreSlideConfig.from_base_slide_config_and_animation_indices(
                self._base_slide_config,
                self._start_animation,
                self._current_animation,
            )
        )

    def _save_slides(
        self,
        use_cache: bool = True,
        flush_cache: bool = False,
        skip_reversing: bool = False,
        max_files_cached: int = 100,
    ) -> None:
        """Save slides to disk."""
        from .manim import ManimSlide

        if not isinstance(self, ManimSlide):
            return

        slides_dir = Path("slides")
        slides_dir.mkdir(exist_ok=True)

        files_dir = slides_dir / "files" / self.__class__.__name__
        files_dir.mkdir(parents=True, exist_ok=True)

        if flush_cache:
            shutil.rmtree(files_dir, ignore_errors=True)
            files_dir.mkdir(parents=True, exist_ok=True)

        slides_data = []

        for i, pre_slide_config in enumerate(self.pre_slide_configs):
            slide_data = {
                "index": i,
                "start": pre_slide_config.start,
                "end": pre_slide_config.end,
                "loop": pre_slide_config.loop,
                "notes": pre_slide_config.notes,
            }

            if pre_slide_config.static_image is not None:
                dst_file = files_dir / f"slide_{i:03d}.png"
                slide_data["src"] = str(dst_file.relative_to(slides_dir))

                if not use_cache or not dst_file.exists():
                    process_static_image(pre_slide_config.static_image, dst_file)
            else:
                dst_file = files_dir / f"slide_{i:03d}.mp4"
                slide_data["src"] = str(dst_file.relative_to(slides_dir))

                if not use_cache or not dst_file.exists():
                    self._process_video_slide(
                        pre_slide_config, dst_file, skip_reversing
                    )

            slides_data.append(slide_data)

        config_file = slides_dir / f"{self.__class__.__name__}.json"
        with open(config_file, "w") as f:
            json.dump(slides_data, f, indent=2)

        self.logger.info(f"Generated {len(slides_data)} slides to '{files_dir}'")
        self.logger.info(
            f"Slide '{self.__class__.__name__}' configuration written in '{config_file}'"
        )

    def start_skip_animations(self) -> None:
        """
        Start skipping animations.

        This automatically applies ``skip_animations=True``
        to all subsequent calls to :meth:`next_slide`.

        This is useful when you want to skip animations from multiple slides in a row,
        without having to manually set ``skip_animations=True``.
        """
        self._skip_animations = True

    def stop_skip_animations(self) -> None:
        """Stop skipping animations."""
        self._skip_animations = False

    def wipe(
        self,
        *args: Any,
        direction: np.ndarray = LEFT,
        return_animation: bool = False,
        **kwargs: Any,
    ) -> Wipe | None:
        """
        Play a wipe animation that will shift all the current objects outside of the
        current scene's scope, and all the future objects inside.

        :param args: Positional arguments passed to
            :class:`Wipe<manim_slides.slide.animation.Wipe>`.
        :param direction: The wipe direction, that will be scaled by the scene size.
        :param return_animation: If set, return the animation instead of
            playing it. This is useful to combine multiple animations with this one.
        :param kwargs: Keyword arguments passed to
            :class:`Wipe<manim_slides.slide.animation.Wipe>`.

        Examples
        --------
        .. manim-slides:: WipeExample

            from manim import *
            from manim_slides import Slide

            class WipeExample(Slide):
                def construct(self):
                    circle = Circle(radius=3, color=BLUE)
                    square = Square()
                    text = Text("This is a wipe example").next_to(square, DOWN)
                    beautiful = Text("Beautiful, no?")

                    self.play(FadeIn(circle))
                    self.next_slide()

                    self.wipe(circle, Group(square, text))
                    self.next_slide()

                    self.wipe(Group(square, text), beautiful, direction=UP)
                    self.next_slide()

                    anim = self.wipe(
                        beautiful,
                        circle,
                        direction=DOWN + RIGHT,
                        return_animation=True
                    )
                    self.play(anim)

        """
        from .animation import Wipe

        shift_amount = np.asarray(direction) * np.array(
            [self._frame_width, self._frame_height, 0.0]
        )

        kwargs.setdefault("shift", shift_amount)

        animation = Wipe(
            *args,
            **kwargs,
        )

        if return_animation:
            return animation

        self.play(animation)
        return None

    def zoom(
        self,
        *args: Any,
        return_animation: bool = False,
        **kwargs: Any,
    ) -> Zoom | None:
        """
        Play a zoom animation that will fade out all the current objects, and fade in
        all the future objects. Objects are faded in a direction that goes towards the
        camera.

        :param args: Positional arguments passed to
            :class:`Zoom<manim_slides.slide.animation.Zoom>`.
        :param return_animation: If set, return the animation instead of
            playing it. This is useful to combine multiple animations with this one.
        :param kwargs: Keyword arguments passed to
            :class:`Zoom<manim_slides.slide.animation.Zoom>`.

        Examples
        --------
        .. manim-slides:: ZoomExample

            from manim import *
            from manim_slides import Slide

            class ZoomExample(Slide):
                def construct(self):
                    circle = Circle(radius=3, color=BLUE)
                    square = Square()

                    self.play(FadeIn(circle))
                    self.next_slide()

                    self.zoom(circle, square)
                    self.next_slide()

                    anim = self.zoom(
                        square,
                        circle,
                        out=True,
                        scale=10.0,
                        return_animation=True
                    )
                    self.play(anim)

        """
        from .animation import Zoom

        animation = Zoom(*args, **kwargs)

        if return_animation:
            return animation

        self.play(animation)
        return None
