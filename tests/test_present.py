from collections.abc import Iterator
from pathlib import Path

import pytest
from click.testing import CliRunner
from qtpy.QtWidgets import QApplication

from manim_slides.present import present


@pytest.fixture(autouse=True)
def auto_shutdown_qapp() -> Iterator[None]:
    if app := QApplication.instance():
        app.quit()

    yield

    if app := QApplication.instance():
        app.quit()


@pytest.fixture(scope="session")
def args(slides_folder: Path) -> Iterator[tuple[str, ...]]:
    yield ("--folder", str(slides_folder), "--skip-all", "--playback-rate", "25")


def test_present(args: tuple[str, ...]) -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        results = runner.invoke(present, ["BasicSlide", *args])

        assert results.exit_code == 0
        assert results.stdout == ""


def test_present_unexisting_slide(args: tuple[str, ...]) -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        results = runner.invoke(present, ["UnexistingSlide", *args])

        assert results.exit_code != 0
        assert "UnexistingSlide.json does not exist" in results.stdout


def test_present_full_screen(args: tuple[str, ...]) -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        results = runner.invoke(present, ["BasicSlide", "--fullscreen", *args])

        assert results.exit_code == 0
        assert results.stdout == ""


def test_present_hide_mouse(args: tuple[str, ...]) -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        results = runner.invoke(present, ["BasicSlide", "--hide-mouse", *args])

        assert results.exit_code == 0
        assert results.stdout == ""


def test_present_ignore_aspect_ratio(args: tuple[str, ...]) -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        results = runner.invoke(
            present, ["BasicSlide", "--aspect-ratio", "ignore", *args]
        )

        assert results.exit_code == 0
        assert results.stdout == ""


def test_present_start_at(args: tuple[str, ...]) -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        results = runner.invoke(present, ["BasicSlide", "--start-at", "-1,-1", *args])

        assert results.exit_code == 0
        assert results.stdout == ""


def test_present_start_at_invalid(args: tuple[str, ...]) -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        results = runner.invoke(present, ["BasicSlide", "--start-at", "0,1234", *args])

        assert results.exit_code == 0
        assert "Could not set presentation index to 1234"


def test_present_start_at_scene_number(args: tuple[str, ...]) -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        results = runner.invoke(
            present, ["BasicSlide", "BasicSlide", "--start-at-scene-number", "1", *args]
        )

        assert results.exit_code == 0
        assert results.stdout == ""


def test_present_start_at_slide_number(args: tuple[str, ...]) -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        results = runner.invoke(
            present, ["BasicSlide", "--start-at-slide-number", "1", *args]
        )

        assert results.exit_code == 0
        assert results.stdout == ""


def test_present_set_screen(args: tuple[str, ...]) -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        results = runner.invoke(present, ["BasicSlide", "--screen", "0", *args])

        assert results.exit_code == 0
        assert results.stdout == ""


@pytest.mark.skip(reason="Fails when running the whole test suite.")
def test_present_set_invalid_screen(args: tuple[str, ...]) -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        results = runner.invoke(present, ["BasicSlide", "--screen", "999", *args])

        assert results.exit_code == 0
        assert "Invalid screen number 999" in results.stdout
