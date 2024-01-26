import random
import shutil
from pathlib import Path

import numpy as np
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
    Text,
)
from packaging import version
from pydantic import ValidationError

from manim_slides.config import PresentationConfig
from manim_slides.defaults import FOLDER_PATH
from manim_slides.render import render
from manim_slides.slide.manim import Slide


@pytest.mark.parametrize(
    "renderer",
    [
        "--CE",
        pytest.param(
            "--GL",
            marks=pytest.mark.skipif(
                version.parse(np.__version__) >= version.parse("1.25"),
                reason="ManimGL requires numpy<1.25, which is outdate",
            ),
        ),
    ],
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
            render, [renderer, str(slides_file), "BasicSlide", "-ql"]
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


def assert_constructs(cls: type) -> type:
    class Wrapper:
        @classmethod
        def test_construct(_) -> None:  # noqa: N804
            cls().construct()

    return Wrapper


def assert_renders(cls: type) -> type:
    class Wrapper:
        @classmethod
        def test_render(_) -> None:  # noqa: N804
            cls().render()

    return Wrapper


class TestSlide:
    @assert_constructs
    class TestDefaultProperties(Slide):
        def construct(self) -> None:
            assert self._output_folder == FOLDER_PATH
            assert len(self._slides) == 0
            assert self._current_slide == 1
            assert self._start_animation == 0
            assert len(self._canvas) == 0
            assert self._wait_time_between_slides == 0.0

    @assert_renders
    class TestMultipleAnimationsInLastSlide(Slide):
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

    @assert_renders
    class TestFileTooLong(Slide):
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

    @assert_constructs
    class TestLoop(Slide):
        def construct(self) -> None:
            text = Text("Some text")

            self.add(text)

            assert not self._base_slide_config.loop

            self.next_slide(loop=True)
            self.play(text.animate.scale(2))

            assert self._base_slide_config.loop

            self.next_slide(loop=False)

            assert not self._base_slide_config.loop

    @assert_constructs
    class TestAutoNext(Slide):
        def construct(self) -> None:
            text = Text("Some text")

            self.add(text)

            assert not self._base_slide_config.auto_next

            self.next_slide(auto_next=True)
            self.play(text.animate.scale(2))

            assert self._base_slide_config.auto_next

            self.next_slide(auto_next=False)

            assert not self._base_slide_config.auto_next

    @assert_constructs
    class TestLoopAndAutoNextFails(Slide):
        def construct(self) -> None:
            text = Text("Some text")

            self.add(text)

            self.next_slide(loop=True, auto_next=True)
            self.play(text.animate.scale(2))

            with pytest.raises(ValidationError):
                self.next_slide()

    @assert_constructs
    class TestPlaybackRate(Slide):
        def construct(self) -> None:
            text = Text("Some text")

            self.add(text)

            assert self._base_slide_config.playback_rate == 1.0

            self.next_slide(playback_rate=2.0)
            self.play(text.animate.scale(2))

            assert self._base_slide_config.playback_rate == 2.0

    @assert_constructs
    class TestReversedPlaybackRate(Slide):
        def construct(self) -> None:
            text = Text("Some text")

            self.add(text)

            assert self._base_slide_config.reversed_playback_rate == 1.0

            self.next_slide(reversed_playback_rate=2.0)
            self.play(text.animate.scale(2))

            assert self._base_slide_config.reversed_playback_rate == 2.0

    @assert_constructs
    class TestNotes(Slide):
        def construct(self) -> None:
            text = Text("Some text")

            self.add(text)

            assert self._base_slide_config.notes == ""

            self.next_slide(notes="test")
            self.play(text.animate.scale(2))

            assert self._base_slide_config.notes == "test"

    @assert_constructs
    class TestWipe(Slide):
        def construct(self) -> None:
            text = Text("Some text")
            bye = Text("Bye")

            self.add(text)

            assert text in self.mobjects
            assert bye not in self.mobjects

            self.wipe([text], [bye])

            assert text not in self.mobjects
            assert bye in self.mobjects

    @assert_constructs
    class TestZoom(Slide):
        def construct(self) -> None:
            text = Text("Some text")
            bye = Text("Bye")

            self.add(text)

            assert text in self.mobjects
            assert bye not in self.mobjects

            self.zoom([text], [bye])

            assert text not in self.mobjects
            assert bye in self.mobjects

    @assert_constructs
    class TestPlay(Slide):
        def construct(self) -> None:
            assert self._current_animation == 0
            circle = Circle(color=BLUE)
            dot = Dot()

            self.play(GrowFromCenter(circle))
            assert self._current_animation == 1
            self.play(FadeIn(dot))
            assert self._current_animation == 2

    @assert_constructs
    class TestWaitTimeBetweenSlides(Slide):
        def construct(self) -> None:
            self._wait_time_between_slides = 1.0
            assert self._current_animation == 0
            circle = Circle(color=BLUE)
            self.play(GrowFromCenter(circle))
            assert self._current_animation == 1
            self.next_slide()
            assert self._current_animation == 2  # self.wait = +1

    @assert_constructs
    class TestNextSlide(Slide):
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

    @assert_constructs
    class TestCanvas(Slide):
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
