import warnings
from pathlib import Path

import pytest
from click.testing import CliRunner

from manim_slides.__main__ import cli


def test_help() -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        results = runner.invoke(cli, ["-S", "--help"])

        assert results.exit_code == 0

        results = runner.invoke(cli, ["-S", "-h"])

        assert results.exit_code == 0
        assert "Usage: cli [OPTIONS] COMMAND [ARGS]..." in results.stdout


def test_defaults_to_present(slides_folder: Path) -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        results = runner.invoke(cli, ["-S", "BasicSlide", "--help"])

        assert results.exit_code == 0
        assert "Usage: cli present" in results.stdout


@pytest.mark.parametrize(
    ["subcommand"], [["present"], ["convert"], ["init"], ["list-scenes"], ["wizard"]]
)
def test_help_subcommand(subcommand: str) -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        results = runner.invoke(cli, ["-S", subcommand, "--help"])

        assert results.exit_code == 0
        assert f"Usage: cli {subcommand}" in results.stdout


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


@pytest.mark.parametrize(("extension",), [("html",)])
def test_convert_data_uri_deprecated(slides_folder: Path, extension: str) -> None:
    runner = CliRunner(mix_stderr=False)

    with runner.isolated_filesystem():
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
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
                    "-cdata_uri=true",
                ],
            )
            assert any(
                "'data_uri' configuration option is deprecated" in str(item.message)
                and item.category is DeprecationWarning
                for item in w
            )
            assert results.exit_code == 0


@pytest.mark.parametrize(
    ("extension", "expected_log"),
    [("html", ""), ("pdf", ""), ("pptx", ""), ("ppt", "WARNING")],
)
def test_convert_auto(slides_folder: Path, extension: str, expected_log: str) -> None:
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
            ],
        )

        assert results.exit_code == 0, expected_log in results.output


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
