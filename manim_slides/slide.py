import platform
import shutil
import subprocess
from pathlib import Path
from typing import (
    Any,
    List,
    Mapping,
    MutableMapping,
    Optional,
    Sequence,
    Tuple,
    ValuesView,
)
from warnings import warn

import numpy as np
from tqdm import tqdm

from .config import PresentationConfig, SlideConfig, SlideType
from .defaults import FOLDER_PATH
from .manim import (
    FFMPEG_BIN,
    LEFT,
    MANIMGL,
    AnimationGroup,
    FadeIn,
    FadeOut,
    Mobject,
    Scene,
    ThreeDScene,
    config,
    logger,
)


def reverse_video_file(src: Path, dst: Path) -> None:
    """Reverses a video file, writting the result to `dst`."""
    command = [str(FFMPEG_BIN), "-y", "-i", str(src), "-vf", "reverse", str(dst)]
    logger.debug(" ".join(command))
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = process.communicate()

    if output:
        logger.debug(output.decode())

    if error:
        logger.debug(error.decode())


class Slide(Scene):  # type:ignore
    """
    Inherits from :class:`Scene<manim.scene.scene.Scene>` and provide necessary tools for slides rendering.
    """

    def __init__(
        self, *args: Any, output_folder: Path = FOLDER_PATH, **kwargs: Any
    ) -> None:
        if MANIMGL:
            Path("videos").mkdir(exist_ok=True)
            kwargs["file_writer_config"] = {
                "break_into_partial_movies": True,
                "output_directory": "",
                "write_to_movie": True,
            }

            kwargs["preview"] = False

        super().__init__(*args, **kwargs)

        self.__output_folder: Path = output_folder
        self.__slides: List[SlideConfig] = []
        self.__current_slide = 1
        self.__current_animation = 0
        self.__loop_start_animation: Optional[int] = None
        self.__pause_start_animation = 0
        self.__canvas: MutableMapping[str, Mobject] = {}
        self.__wait_time_between_slides = 0.0

    @property
    def __frame_height(self) -> float:
        """Returns the scene's frame height."""
        if MANIMGL:
            return self.frame_height  # type: ignore
        else:
            return config["frame_height"]  # type: ignore

    @property
    def __frame_width(self) -> float:
        """Returns the scene's frame width."""
        if MANIMGL:
            return self.frame_width  # type: ignore
        else:
            return config["frame_width"]  # type: ignore

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
    def __partial_movie_files(self) -> List[Path]:
        """Returns a list of partial movie files, a.k.a animations."""
        if MANIMGL:
            from manimlib.utils.file_ops import get_sorted_integer_files

            kwargs = {
                "remove_non_integer_files": True,
                "extension": self.file_writer.movie_file_extension,
            }
            files = get_sorted_integer_files(
                self.file_writer.partial_movie_directory, **kwargs
            )
        else:
            files = self.renderer.file_writer.partial_movie_files

        return [Path(file) for file in files]

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

    @property
    def canvas(self) -> MutableMapping[str, Mobject]:
        """
        Returns the canvas associated to the current slide.

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

                    self.play(self.wipe(self.mobjects_without_canvas, square))
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
                    self.play(self.wipe(self.mobjects_without_canvas, []))

        """
        return self.__canvas

    def add_to_canvas(self, **objects: Mobject) -> Mobject:
        """
        Adds objects to the canvas, using key values as names.

        :param objects: A mapping between names and Mobjects.

        .. note::

            This method does not actually do anything in terms of
            animations. You must still call :code:`self.add` or
            play some animation that introduces each Mobject for
            it to appear. The same applies when removing objects.
        """
        self.__canvas.update(objects)

    def remove_from_canvas(self, *names: str) -> None:
        """
        Removes objects from the canvas.
        """
        for name in names:
            self.__canvas.pop(name)

    @property
    def canvas_mobjects(self) -> ValuesView[Mobject]:
        """
        Returns Mobjects contained in the canvas.
        """
        return self.canvas.values()

    @property
    def mobjects_without_canvas(self) -> Sequence[Mobject]:
        """
        Returns the list of objects contained in the scene,
        minus those present in the canvas.
        """
        return [
            mobject for mobject in self.mobjects if mobject not in self.canvas_mobjects
        ]

    @property
    def wait_time_between_slides(self) -> float:
        r"""
        Returns the wait duration (in seconds) added between two slides.

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
        return self.__wait_time_between_slides

    @wait_time_between_slides.setter
    def wait_time_between_slides(self, wait_time: float) -> None:
        self.__wait_time_between_slides = max(wait_time, 0.0)

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

        .. manim-slides:: NextSlideExample

            from manim import *
            from manim_slides import Slide

            class NextSlideExample(Slide):
                def construct(self):
                    text = Text("Hello World!")

                    self.play(FadeIn(text))

                    self.next_slide()
                    self.play(FadeOut(text))
        """
        assert (
            self.__loop_start_animation is None
        ), "You cannot call `self.next_slide()` inside a loop"

        if self.wait_time_between_slides > 0.0:
            self.wait(self.wait_time_between_slides)

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

        .. warning::

            When rendered with RevealJS, loops cannot be in the first nor
            the last slide.

        Examples
        --------

        The following contains one slide that will loop endlessly.

        .. manim-slides:: LoopExample

            from manim import *
            from manim_slides import Slide

            class LoopExample(Slide):
                def construct(self):
                    dot = Dot(color=BLUE, radius=1)

                    self.play(FadeIn(dot))
                    self.next_slide()

                    self.start_loop()

                    self.play(Indicate(dot, scale_factor=2))

                    self.end_loop()

                    self.play(FadeOut(dot))
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

        files_folder = self.__output_folder / "files"

        scene_name = str(self)
        scene_files_folder = files_folder / scene_name

        scene_files_folder.mkdir(parents=True, exist_ok=True)

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

            dst_file = scene_files_folder / src_file.name
            rev_file = scene_files_folder / f"{src_file.stem}_reversed{src_file.suffix}"

            # We only copy animation if it was not present
            if not use_cache or not dst_file.exists():
                shutil.copyfile(src_file, dst_file)

            # We only reverse video if it was not present
            if not use_cache or not rev_file.exists():
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
            f"Copied {len(files)} animations to '{scene_files_folder.absolute()}' and generated reversed animations"
        )

        slide_path = self.__output_folder / f"{scene_name}.json"

        PresentationConfig(
            slides=self.__slides,
            files=files,
            resolution=self.__resolution,
            background_color=self.__background_color,
        ).to_file(slide_path)

        logger.info(
            f"Slide '{scene_name}' configuration written in '{slide_path.absolute()}'"
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

    def wipe(
        self,
        current: Sequence[Mobject] = [],
        future: Sequence[Mobject] = [],
        direction: np.ndarray = LEFT,
        fade_in_kwargs: Mapping[str, Any] = {},
        fade_out_kwargs: Mapping[str, Any] = {},
        **kwargs: Any,
    ) -> AnimationGroup:
        """
        Returns a wipe animation that will shift all the current objects outside
        of the current scene's scope, and all the future objects inside.

        :param current: A sequence of mobjects to remove from the scene.
        :param future: A sequence of mobjects to add to the scene.
        :param direction: The wipe direction.
        :param fade_in_kwargs: Keyword arguments passed to
            :class:`FadeIn<manim.animation.fading.FadeIn>`.
        :param fade_out_kwargs: Keyword arguments passed to
            :class:`FadeOut<manim.animation.fading.FadeOut>`.
        :param kwargs: Keyword arguments passed to
            :class:`AnimationGroup<manim.animation.composition.AnimationGroup>`.

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

                    self.play(self.wipe(circle, Group(square, text)))
                    self.next_slide()

                    self.play(self.wipe(Group(square, text), beautiful, direction=UP))
                    self.next_slide()

                    self.play(self.wipe(beautiful, circle, direction=DOWN + RIGHT))
        """
        shift_amount = np.asarray(direction) * np.array(
            [self.__frame_width, self.__frame_height, 0.0]
        )

        animations = []

        for mobject in future:
            animations.append(FadeIn(mobject, shift=shift_amount, **fade_in_kwargs))

        for mobject in current:
            animations.append(FadeOut(mobject, shift=shift_amount, **fade_out_kwargs))

        return AnimationGroup(*animations, **kwargs)

    def zoom(
        self,
        current: Sequence[Mobject] = [],
        future: Sequence[Mobject] = [],
        scale: float = 4.0,
        out: bool = False,
        fade_in_kwargs: Mapping[str, Any] = {},
        fade_out_kwargs: Mapping[str, Any] = {},
        **kwargs: Any,
    ) -> AnimationGroup:
        """
        Returns a zoom animation that will fade out all the current objects,
        and fade in all the future objects. Objects are faded in a direction
        that goes towards the camera.

        :param current: A sequence of mobjects to remove from the scene.
        :param future: A sequence of mobjects to add to the scene.
        :param scale: How much the objects are scaled (up or down).
        :param out: If set, the objects fade in the opposite direction.
        :param fade_in_kwargs: Keyword arguments passed to
            :class:`FadeIn<manim.animation.fading.FadeIn>`.
        :param fade_out_kwargs: Keyword arguments passed to
            :class:`FadeOut<manim.animation.fading.FadeOut>`.
        :param kwargs: Keyword arguments passed to
            :class:`AnimationGroup<manim.animation.composition.AnimationGroup>`.

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

                    self.play(self.zoom(circle, square))
                    self.next_slide()

                    self.play(self.zoom(square, circle, out=True, scale=10.))
        """
        scale_in = 1.0 / scale
        scale_out = scale

        if out:
            scale_in, scale_out = scale_out, scale_in

        animations = []

        for mobject in future:
            animations.append(FadeIn(mobject, scale=scale_in, **fade_in_kwargs))

        for mobject in current:
            animations.append(FadeOut(mobject, scale=scale_out, **fade_out_kwargs))

        return AnimationGroup(*animations, **kwargs)


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
