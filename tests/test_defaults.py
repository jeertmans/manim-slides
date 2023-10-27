import shutil

from pathlib import Path

from manim_slides.defaults import CONFIG_PATH, FFMPEG_BIN, FOLDER_PATH


def test_folder_path() -> None:
    assert FOLDER_PATH == Path("./slides")


def test_config_path() -> None:
    assert CONFIG_PATH == Path(".manim-slides.toml")


def test_ffmpeg_bin() -> None:
    assert FFMPEG_BIN == Path("ffmpeg")


def test_ffmpeg_bin_exists() -> None:
    assert shutil.which(FFMPEG_BIN) is not None, "If this fails, many other tests will fail"
