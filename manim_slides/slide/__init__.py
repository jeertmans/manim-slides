__all__ = [
    "MANIM",
    "MANIMGL",
    "API_NAME",
    "Slide",
    "ThreeDSlide",
]


import os
import sys


class ManimApiNotFoundError(ImportError):
    """Error raised if specified manim API could be imported."""

    _msg = "Could not import the specified manim API"

    def __init__(self):
        super().__init__(self._msg)


API_NAMES = {
    "manim": "manim",
    "manimce": "manim",
    "manimlib": "manimlib",
    "manimgl": "manimlib",
}

MANIM_API = "MANIM_API"
FORCE_MANIM_API = "FORCE_" + MANIM_API

API = os.environ.get(MANIM_API, "manim").lower()


if API not in API_NAMES:
    raise ImportError(
        f"Specified MANIM_API={API!r} is not in valid options: " f"{API_NAMES}",
    )

API_NAME = API_NAMES[API]

if not os.environ.get(FORCE_MANIM_API):
    if "manim" in sys.modules:
        API_NAME = "manim"
    elif "manimlib" in sys.modules:
        API_NAME = "manimlib"

MANIM = API_NAME == "manim"
MANIMGL = API_NAME == "manimlib"

if MANIM:
    try:
        from .manim import Slide, ThreeDSlide
    except ImportError as e:
        raise ManimApiNotFoundError from e
elif MANIMGL:
    try:
        from .manimgl import Slide, ThreeDSlide
    except ImportError as e:
        raise ManimApiNotFoundError from e
