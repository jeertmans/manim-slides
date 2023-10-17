from pathlib import Path

import pytest
from click.testing import CliRunner

from manim_slides.__main__ import cli


def test_help() -> None:
    runner = CliRunner()
    results = runner.invoke(cli, ["-S", "--help"])

    assert results.exit_code == 0

    results = runner.invoke(cli, ["-S", "-h"])

    assert results.exit_code == 0


def test_defaults_to_present(slides_folder: Path) -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        results = runner.invoke(
            cli, ["BasicSlide", "--folder", str(slides_folder), "-s"]
        )

        assert results.exit_code == 0


def test_present(slides_folder: Path) -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        results = runner.invoke(
            cli, ["present", "BasicSlide", "--folder", str(slides_folder), "-s"]
        )

        assert results.exit_code == 0


@pytest.mark.parametrize(("extension",), [("html",), ("pdf",), ("pptx",)])
def test_convert(slides_folder: Path, extension: str) -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        results = runner.invoke(
            cli,
            [
                "convert",
                "BasicSlide",
                f"basic_example.{extension}",
                "--folder",
                str(slides_folder),
                "--to",
                extension,
            ],
        )

        assert results.exit_code == 0


def test_init() -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        results = runner.invoke(
            cli,
            [
                "init",
                "--force",
            ],
        )

        assert results.exit_code == 0


def test_list_scenes(slides_folder: Path) -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        results = runner.invoke(
            cli,
            [
                "list-scenes",
                "--folder",
                str(slides_folder),
            ],
        )

        assert results.exit_code == 0
        assert "BasicSlide" in results.output


def test_wizard() -> None:
    # TODO
    pass
