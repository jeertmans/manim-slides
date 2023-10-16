import subprocess
import sys
from pathlib import Path

import click
import pytest
from click.testing import CliRunner
from manim import Text
from manim.__main__ import main as manim_cli
from pydantic import ValidationError

from manim_slides.config import PresentationConfig
from manim_slides.slide.manim import Slide
from manim_slides.defaults import FOLDER_PATH


@click.command(
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    )
)
@click.pass_context
def manimgl_cli(ctx: click.Context) -> None:
    subprocess.run([sys.executable, "-m", "manimlib", *ctx.args])


cli = pytest.mark.parametrize(
    ["cli"],
    [
        [manim_cli],
        pytest.param(manimgl_cli, marks=pytest.mark.xfail(reason="OpenGL issue")),
    ],
)


def assert_construct(cls: type) -> type:
    class Wrapper:
        @classmethod
        def test_construct(_) -> None:
            cls().construct()

    return Wrapper


@cli
def test_render_basic_examples(
    cli: click.Command, slides_file: Path, presentation_config: PresentationConfig
) -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        results = runner.invoke(cli, [str(slides_file), "BasicSlide", "-ql"])

        assert results.exit_code == 0

        local_slides_folder = Path("slides")

        assert local_slides_folder.exists()

        local_config_file = local_slides_folder / "BasicSlide.json"

        assert local_config_file.exists()

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


class TestSlide:
    @assert_construct
    class TestDefaultProperties(Slide):
        def construct(self) -> None:
            assert self._output_folder == FOLDER_PATH
            assert len(self._slides) == 0
            assert self._current_slide == 1
            assert self._loop_start_animation is None
            assert self._pause_start_animation == 0
            assert len(self._canvas) == 0
            assert self._wait_time_between_slides == 0.0

    @assert_construct
    class TestLoop(Slide):
        def construct(self) -> None:
            text = Text("Some text")

            self.add(text)

            self.start_loop()
            self.play(text.animate.scale(2))
            self.end_loop()

            with pytest.raises(AssertionError):
                self.end_loop()

            self.start_loop()
            with pytest.raises(AssertionError):
                self.start_loop()

            with pytest.raises(ValidationError):
                self.end_loop()

    @assert_construct
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

    @assert_construct
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

    @assert_construct
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
