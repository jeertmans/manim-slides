import contextlib
import os
import random
import shutil
import sys
import tempfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any, Union

import pytest
from click.testing import CliRunner
from manim import (
    BLUE,
    DOWN,
    LEFT,
    ORIGIN,
    RIGHT,
    UP,
    Circle,
    Dot,
    FadeIn,
    GrowFromCenter,
    Square,
    Text,
)
from manim.renderer.opengl_renderer import OpenGLRenderer

from manim_slides.config import PresentationConfig
from manim_slides.defaults import FOLDER_PATH
from manim_slides.render import render
from manim_slides.slide.manim import Slide as CESlide

if sys.version_info < (3, 10):

    class _GLSlide:
        def construct(self) -> None:
            pass

        def render(self) -> None:
            pass

    GLSlide = pytest.param(
        _GLSlide,
        marks=pytest.mark.skip(reason="See https://github.com/3b1b/manim/issues/2263"),
    )
else:
    from manim_slides.slide.manimlib import Slide as GLSlide

    _GLSlide = GLSlide


class CEGLSlide(CESlide):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, renderer=OpenGLRenderer(), **kwargs)


SlideType = Union[type[CESlide], type[_GLSlide], type[CEGLSlide]]
Slide = Union[CESlide, _GLSlide, CEGLSlide]


@pytest.mark.parametrize(
    "renderer",
    [
        "--CE",
        pytest.param(
            "--GL",
            marks=pytest.mark.skipif(
                sys.version_info < (3, 10),
                reason="See https://github.com/3b1b/manim/issues/2263.",
            ),
        ),
        "--CE --renderer=opengl",
    ],
    ids=("CE", "GL", "CE(GL)"),
)
def test_render_basic_slide(
    renderer: str,
    slides_file: Path,
    presentation_config: PresentationConfig,
    manimgl_config: Path,
) -> None:
    runner = CliRunner()

    with runner.isolated_filesystem() as tmp_dir:
        shutil.copy(manimgl_config, tmp_dir)
        results = runner.invoke(
            render, [*renderer.split(" "), str(slides_file), "BasicSlide", "-ql"]
        )

        assert results.exit_code == 0, results

        local_slides_folder = (Path(tmp_dir) / "slides").resolve(strict=True)

        local_config_file = (local_slides_folder / "BasicSlide.json").resolve(
            strict=True
        )

        local_presentation_config = PresentationConfig.from_file(local_config_file)

        assert len(local_presentation_config.slides) == len(presentation_config.slides)

        assert (
            local_presentation_config.background_color
            == presentation_config.background_color
        )

        assert (
            local_presentation_config.background_color
            == presentation_config.background_color
        )

        assert local_presentation_config.resolution == presentation_config.resolution


def test_clear_cache(
    slides_file: Path,
) -> None:
    runner = CliRunner()

    with runner.isolated_filesystem() as tmp_dir:
        local_media_folder = (
            Path(tmp_dir)
            / "media"
            / "videos"
            / slides_file.stem
            / "480p15"
            / "partial_movie_files"
            / "BasicSlide"
        )
        local_slides_folder = Path(tmp_dir) / "slides"

        assert not local_media_folder.exists()
        assert not local_slides_folder.exists()
        results = runner.invoke(render, [str(slides_file), "BasicSlide", "-ql"])

        assert results.exit_code == 0, results
        assert local_media_folder.is_dir() and list(local_media_folder.iterdir())
        assert local_slides_folder.exists()

        results = runner.invoke(
            render, [str(slides_file), "BasicSlide", "-ql", "--flush_cache"]
        )

        assert results.exit_code == 0, results
        assert local_media_folder.is_dir() and not list(local_media_folder.iterdir())
        assert local_slides_folder.exists()

        results = runner.invoke(
            render, [str(slides_file), "BasicSlide", "-ql", "--disable_caching"]
        )

        assert results.exit_code == 0, results
        assert local_media_folder.is_dir() and list(local_media_folder.iterdir())
        assert local_slides_folder.exists()

        results = runner.invoke(
            render,
            [
                str(slides_file),
                "BasicSlide",
                "-ql",
                "--disable_caching",
                "--flush_cache",
            ],
        )

        assert results.exit_code == 0, results
        assert local_media_folder.is_dir() and not list(local_media_folder.iterdir())
        assert local_slides_folder.exists()


@pytest.mark.parametrize(
    "renderer",
    [
        "--CE",
        pytest.param(
            "--GL",
            marks=pytest.mark.skipif(
                sys.version_info < (3, 10),
                reason="See https://github.com/3b1b/manim/issues/2263.",
            ),
        ),
    ],
)
@pytest.mark.parametrize(
    ("klass", "skip_reversing"),
    [("BasicSlide", False), ("BasicSlideSkipReversing", True)],
)
def test_skip_reversing(
    renderer: str,
    slides_file: Path,
    manimgl_config: Path,
    klass: str,
    skip_reversing: bool,
) -> None:
    runner = CliRunner()

    with runner.isolated_filesystem() as tmp_dir:
        shutil.copy(manimgl_config, tmp_dir)
        results = runner.invoke(render, [renderer, str(slides_file), klass, "-ql"])

        assert results.exit_code == 0, results

        local_slides_folder = (Path(tmp_dir) / "slides").resolve(strict=True)

        local_config_file = (local_slides_folder / f"{klass}.json").resolve(strict=True)

        local_presentation_config = PresentationConfig.from_file(local_config_file)

        for slide in local_presentation_config.slides:
            if skip_reversing:
                assert slide.file == slide.rev_file
            else:
                assert slide.file != slide.rev_file


def init_slide(cls: SlideType) -> Slide:
    if issubclass(cls, CESlide):
        return cls()
    elif issubclass(cls, GLSlide):
        from manimlib.config import parse_cli

        _args = parse_cli()
        return cls()

    raise ValueError(f"Unsupported class {cls}")


parametrize_base_cls = pytest.mark.parametrize(
    "base_cls", (CESlide, GLSlide, CEGLSlide), ids=("CE", "GL", "CE(GL)")
)


def assert_constructs(cls: SlideType) -> None:
    init_slide(cls).construct()


@contextlib.contextmanager
def tmp_cwd() -> Iterator[str]:
    cwd = os.getcwd()
    tmp_dir = tempfile.mkdtemp()

    os.chdir(tmp_dir)

    try:
        yield tmp_dir
    finally:
        os.chdir(cwd)


def assert_renders(cls: SlideType) -> None:
    with tmp_cwd():
        init_slide(cls).render()


class TestSlide:
    def test_default_properties(self) -> None:
        @assert_constructs
        class _(CESlide):
            def construct(self) -> None:
                assert self._output_folder == FOLDER_PATH
                assert len(self._slides) == 0
                assert self._current_slide == 1
                assert self._start_animation == 0
                assert len(self._canvas) == 0
                assert self._wait_time_between_slides == 0.0

    @parametrize_base_cls
    def test_frame_height(self, base_cls: SlideType) -> None:
        @assert_constructs
        class _(base_cls):  # type: ignore
            def construct(self) -> None:
                assert self._frame_height > 0 and isinstance(self._frame_height, float)

    @parametrize_base_cls
    def test_frame_width(self, base_cls: SlideType) -> None:
        @assert_constructs
        class _(base_cls):  # type: ignore
            def construct(self) -> None:
                assert self._frame_width > 0 and isinstance(self._frame_width, float)

    @parametrize_base_cls
    def test_resolution(self, base_cls: SlideType) -> None:
        @assert_constructs
        class _(base_cls):  # type: ignore
            def construct(self) -> None:
                pw, ph = self._resolution
                assert isinstance(pw, int) and pw > 0
                assert isinstance(ph, int) and ph > 0

    @parametrize_base_cls
    def test_backround_color(self, base_cls: SlideType) -> None:
        @assert_constructs
        class _(base_cls):  # type: ignore
            def construct(self) -> None:
                assert self._background_color in ["#000000", "#000"]  # DEFAULT

    def test_multiple_animations_in_last_slide(self) -> None:
        @assert_renders
        class _(CESlide):
            """Check against solution for issue #161."""

            def construct(self) -> None:
                circle = Circle(color=BLUE)
                dot = Dot()

                self.play(GrowFromCenter(circle))
                self.play(FadeIn(dot))
                self.next_slide()

                self.play(dot.animate.move_to(RIGHT))
                self.play(dot.animate.move_to(UP))
                self.play(dot.animate.move_to(LEFT))
                self.play(dot.animate.move_to(DOWN))

    def test_file_too_long(self) -> None:
        @assert_renders
        class _(CESlide):
            """Check against solution for issue #123."""

            def construct(self) -> None:
                circle = Circle(radius=3, color=BLUE)
                dot = Dot()
                self.play(GrowFromCenter(circle), run_time=0.1)

                for _ in range(30):
                    direction = (random.random() - 0.5) * LEFT + (
                        random.random() - 0.5
                    ) * UP
                    self.play(dot.animate.move_to(direction), run_time=0.1)
                    self.play(dot.animate.move_to(ORIGIN), run_time=0.1)

    def test_loop(self) -> None:
        @assert_constructs
        class _(CESlide):
            def construct(self) -> None:
                text = Text("Some text")

                self.add(text)

                assert not self._base_slide_config.loop

                self.next_slide(loop=True)
                self.play(text.animate.scale(2))

                assert self._base_slide_config.loop

                self.next_slide(loop=False)

                assert not self._base_slide_config.loop

    def test_auto_next(self) -> None:
        @assert_constructs
        class _(CESlide):
            def construct(self) -> None:
                text = Text("Some text")

                self.add(text)

                assert not self._base_slide_config.auto_next

                self.next_slide(auto_next=True)
                self.play(text.animate.scale(2))

                assert self._base_slide_config.auto_next

                self.next_slide(auto_next=False)

                assert not self._base_slide_config.auto_next

    def test_loop_and_auto_next_succeeds(self) -> None:
        @assert_constructs
        class _(CESlide):
            def construct(self) -> None:
                text = Text("Some text")

                self.add(text)

                self.next_slide(loop=True, auto_next=True)
                self.play(text.animate.scale(2))

                self.next_slide()

    def test_playback_rate(self) -> None:
        @assert_constructs
        class _(CESlide):
            def construct(self) -> None:
                text = Text("Some text")

                self.add(text)

                assert self._base_slide_config.playback_rate == 1.0

                self.next_slide(playback_rate=2.0)
                self.play(text.animate.scale(2))

                assert self._base_slide_config.playback_rate == 2.0

    def test_reversed_playback_rate(self) -> None:
        @assert_constructs
        class _(CESlide):
            def construct(self) -> None:
                text = Text("Some text")

                self.add(text)

                assert self._base_slide_config.reversed_playback_rate == 1.0

                self.next_slide(reversed_playback_rate=2.0)
                self.play(text.animate.scale(2))

                assert self._base_slide_config.reversed_playback_rate == 2.0

    def test_notes(self) -> None:
        @assert_constructs
        class _(CESlide):
            def construct(self) -> None:
                text = Text("Some text")

                self.add(text)

                assert self._base_slide_config.notes == ""

                self.next_slide(notes="test")
                self.play(text.animate.scale(2))

                assert self._base_slide_config.notes == "test"

    def test_wipe(self) -> None:
        @assert_constructs
        class _(CESlide):
            def construct(self) -> None:
                text = Text("Some text")
                bye = Text("Bye")

                self.add(text)

                assert text in self.mobjects
                assert bye not in self.mobjects

                self.wipe([text], [bye])

                assert text not in self.mobjects
                assert bye in self.mobjects

    def test_zoom(self) -> None:
        @assert_constructs
        class _(CESlide):
            def construct(self) -> None:
                text = Text("Some text")
                bye = Text("Bye")

                self.add(text)

                assert text in self.mobjects
                assert bye not in self.mobjects

                self.zoom([text], [bye])

                assert text not in self.mobjects
                assert bye in self.mobjects

    def test_animation_count(self) -> None:
        @assert_constructs
        class _(CESlide):
            def construct(self) -> None:
                assert self._current_animation == 0
                circle = Circle(color=BLUE)
                dot = Dot()

                self.play(GrowFromCenter(circle))
                assert self._current_animation == 1
                self.play(FadeIn(dot))
                assert self._current_animation == 2

    def test_wait_time_between_slides(self) -> None:
        @assert_constructs
        class _(CESlide):
            def construct(self) -> None:
                self._wait_time_between_slides = 1.0
                assert self._current_animation == 0
                circle = Circle(color=BLUE)
                self.play(GrowFromCenter(circle))
                assert self._current_animation == 1
                self.next_slide()
                assert self._current_animation == 2  # self.wait = +1

    def test_next_slide(self) -> None:
        @assert_constructs
        class _(CESlide):
            def construct(self) -> None:
                assert self._current_slide == 1
                self.next_slide()
                assert self._current_slide == 1
                circle = Circle(color=BLUE)
                self.play(GrowFromCenter(circle))
                self.next_slide()
                assert self._current_slide == 2
                self.next_slide()
                assert self._current_slide == 2

    def test_next_slide_skip_animations(self) -> None:
        class Foo(CESlide):
            def construct(self) -> None:
                circle = Circle(color=BLUE)
                self.play(GrowFromCenter(circle))
                assert not self._base_slide_config.skip_animations
                self.next_slide(skip_animations=True)
                square = Square(color=BLUE)
                self.play(GrowFromCenter(square))
                assert self._base_slide_config.skip_animations
                self.next_slide()
                assert not self._base_slide_config.skip_animations
                self.play(GrowFromCenter(square))

        class Bar(CESlide):
            def construct(self) -> None:
                circle = Circle(color=BLUE)
                self.play(GrowFromCenter(circle))
                assert not self._base_slide_config.skip_animations
                self.next_slide(skip_animations=False)
                square = Square(color=BLUE)
                self.play(GrowFromCenter(square))
                assert not self._base_slide_config.skip_animations
                self.next_slide()
                assert not self._base_slide_config.skip_animations
                self.play(GrowFromCenter(square))

        with tmp_cwd() as tmp_dir:
            init_slide(Foo).render()
            init_slide(Bar).render()

            slides_folder = Path(tmp_dir) / "slides"

            assert slides_folder.exists()

            slide_file = slides_folder / "Foo.json"

            config = PresentationConfig.from_file(slide_file)

            assert len(config.slides) == 2

            slide_file = slides_folder / "Bar.json"

            config = PresentationConfig.from_file(slide_file)

            assert len(config.slides) == 3

    def test_canvas(self) -> None:
        @assert_constructs
        class _(CESlide):
            def construct(self) -> None:
                text = Text("Some text")
                bye = Text("Bye")

                assert len(self.canvas) == 0

                self.add(text)

                assert len(self.canvas) == 0

                self.add_to_canvas(text=text)

                assert len(self.canvas) == 1

                self.add(bye)

                assert len(self.canvas) == 1

                assert text not in self.mobjects_without_canvas
                assert bye in self.mobjects_without_canvas

                self.remove(text)

                assert len(self.canvas) == 1

                self.add_to_canvas(bye=bye)

                assert len(self.canvas) == 2

                self.remove_from_canvas("text", "bye")

                assert len(self.canvas) == 0

                with pytest.raises(KeyError):
                    self.remove_from_canvas("text")
