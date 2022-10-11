import platform
from typing import Tuple

import cv2

__all__ = [
    "FONT_ARGS",
    "FOLDER_PATH",
    "CONFIG_PATH",
    "RIGHT_ARROW_KEY_CODE",
    "LEFT_ARROW_KEY_CODE",
]

FONT_ARGS: Tuple[int, int, int, int, int] = (
    cv2.FONT_HERSHEY_SIMPLEX,  # type: ignore
    1,
    255,
    1,
    cv2.LINE_AA,  # type: ignore
)
FOLDER_PATH: str = "./slides"
CONFIG_PATH: str = ".manim-slides.json"

if platform.system() == "Windows":
    RIGHT_ARROW_KEY_CODE: int = 2555904
    LEFT_ARROW_KEY_CODE: int = 2424832
elif platform.system() == "Darwin":
    RIGHT_ARROW_KEY_CODE = 63235
    LEFT_ARROW_KEY_CODE = 63234
else:
    RIGHT_ARROW_KEY_CODE = 65363
    LEFT_ARROW_KEY_CODE = 65361
