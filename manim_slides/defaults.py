import os
from pathlib import Path

FOLDER_PATH: Path = Path("./slides")
CONFIG_PATH: Path = Path(".manim-slides.toml")
CONFIG_FILENAME: str = ".manim-slides.toml"

# Global config: ~/.config/manim-slides/config.toml (XDG-compatible)
GLOBAL_CONFIG_DIR: Path = Path(
    os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")
) / "manim-slides"
GLOBAL_CONFIG_PATH: Path = GLOBAL_CONFIG_DIR / "config.toml"