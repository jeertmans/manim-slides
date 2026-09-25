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
        assert "UnexistingSlide.json does not exist" in results.output


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


def test_present_start_at_invalid(
    args: tuple[str, ...], monkeypatch: pytest.MonkeyPatch
) -> None:
    runner = CliRunner()

    # The "manim-slides" logger is a process-wide singleton whose level other
    # CLI invocations (via `--verbosity`) may have raised, and whose captured
    # output may be reformatted (e.g., wrapped) in ways that are hard to
    # match reliably. Instead, the call itself is observed directly.
    warnings = []
    monkeypatch.setattr("manim_slides.present.player.logger.warning", warnings.append)

    with runner.isolated_filesystem():
        results = runner.invoke(present, ["BasicSlide", "--start-at", "0,1234", *args])

        assert results.exit_code == 0
        assert any("Could not set slide index to 1234" in msg for msg in warnings)


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


def test_present_invalid_explicit_config(args: tuple[str, ...]) -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        with open(".manim-slides.toml", "w") as f:
            f.write("defaults = 5")

        results = runner.invoke(
            present, ["BasicSlide", "--config", ".manim-slides.toml", *args]
        )

        assert results.exit_code != 0
        assert "Invalid defaults" in results.output


def test_present_invalid_local_config_is_skipped(
    args: tuple[str, ...], caplog: pytest.LogCaptureFixture
) -> None:
    """An invalid config found in the folder tree only warns, it does not fail."""
    runner = CliRunner()

    with runner.isolated_filesystem():
        with open(".manim-slides.toml", "w") as f:
            f.write("defaults = 5")

        # Not passing --config, so the file is only discovered by walking
        # up the folder tree, and errors are downgraded to warnings.
        with caplog.at_level("WARNING", logger="manim-slides"):
            results = runner.invoke(present, ["BasicSlide", *args])

        assert results.exit_code == 0
        assert any(
            "Ignoring invalid configuration file" in record.message
            for record in caplog.records
        )
