__all__ = [
    "API_NAME",
    "MANIM",
    "MANIMGL",
    "Slide",
    "ThreeDSlide",
]


import os
import sys


class ManimApiNotFoundError(ImportError):
    """Error raised if specified manim API could be imported."""

    _msg = "Could not import the specified manim API"

    def __init__(self) -> None:
        super().__init__(self._msg)


API_NAMES = {
    "manim": "manim",
    "manimce": "manim",
    "manimlib": "manimlib",
    "manimgl": "manimlib",
}

MANIM_API: str = "MANIM_API"
FORCE_MANIM_API: str = "FORCE_" + MANIM_API

API: str = os.environ.get(MANIM_API, "manim").lower()


if API not in API_NAMES:
    raise ImportError(
        f"Specified MANIM_API={API!r} is not in valid options: {API_NAMES}",
    )

API_NAME = API_NAMES[API]

if not os.environ.get(FORCE_MANIM_API):
    if "manim" in sys.modules:
        API_NAME = "manim"
    elif "manimlib" in sys.modules:
        API_NAME = "manimlib"

MANIM: bool = API_NAME == "manim"
MANIMGL: bool = API_NAME == "manimlib"

if MANIM:
    try:
        from .manim import Slide, ThreeDSlide
    except ImportError as e:
        raise ManimApiNotFoundError from e
elif MANIMGL:
    try:
        from .manimlib import Slide, ThreeDSlide
    except ImportError as e:
        raise ManimApiNotFoundError from e
else:
    raise ManimApiNotFoundError
