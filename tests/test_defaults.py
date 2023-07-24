from manim_slides.defaults import CONFIG_PATH, FFMPEG_BIN, FOLDER_PATH


def test_folder_path() -> None:
    assert FOLDER_PATH == "./slides"


def test_config_path() -> None:
    assert CONFIG_PATH == ".manim-slides.json"


def test_ffmpeg_bin() -> None:
    assert FFMPEG_BIN == "ffmpeg"
