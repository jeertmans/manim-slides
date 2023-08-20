from pathlib import Path

import pytest
from click.testing import CliRunner
from manim import Text
from manim.__main__ import main as cli
from pydantic import ValidationError

from manim_slides.slide import Slide


def assert_construct(cls: type) -> type:
    class Wrapper:
        @classmethod
        def test_construct(_) -> None:
            cls().construct()

    return Wrapper


def test_render_basic_examples(slides_file: Path, slides_folder: Path) -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        results = runner.invoke(cli, [str(slides_file), "BasicSlide", "-ql"])

        assert results.exit_code == 0

        local_slides_folder = Path("slides")

        assert local_slides_folder.exists()

        local_config_file = local_slides_folder / "BasicSlide.json"

        assert local_config_file.exists()

        config_file = slides_folder / "BasicSlide.json"
        expected = local_config_file.read_text().strip()
        got = config_file.read_text().strip()

        assert (
            expected == got
        ), f"Mismatch between {local_config_file} and {config_file}"

        expected_files = list((slides_folder / "files" / "BasicSlide").iterdir())
        got_files = list((local_slides_folder / "files" / "BasicSlide").iterdir())

        # TODO: when Python >= 3.10, replace with zip(..., ..., strict=True)
        assert len(got_files) == len(expected_files)

        for expected_file, got_file in zip(expected_files, got_files):
            assert expected_file.name == got_file.name


class TestSlide:
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

            self.play(self.wipe([text], [bye]))

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

            self.play(self.zoom([text], [bye]))

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
