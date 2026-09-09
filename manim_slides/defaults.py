from pathlib import Path

from platformdirs import user_config_path

FOLDER_PATH: Path = Path("./slides")
CONFIG_PATH: Path = Path(".manim-slides.toml")
GLOBAL_CONFIG_DIR: Path = user_config_path("manim-slides")
GLOBAL_CONFIG_PATH: Path = GLOBAL_CONFIG_DIR / "manim-slides.toml"
