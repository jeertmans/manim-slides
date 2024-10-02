from pathlib import Path

from manim_slides.defaults import CONFIG_PATH, FOLDER_PATH


def test_folder_path() -> None:
    assert FOLDER_PATH == Path("./slides")


def test_config_path() -> None:
    assert CONFIG_PATH == Path(".manim-slides.toml")
