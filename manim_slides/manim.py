import sys
from importlib.util import find_spec

__all__ = [
    # Constants
    "FFMPEG_BIN",
    "LEFT",
    "MANIM",
    "MANIM_PACKAGE_NAME",
    "MANIM_AVAILABLE",
    "MANIM_IMPORTED",
    "MANIMGL",
    "MANIMGL_PACKAGE_NAME",
    "MANIMGL_AVAILABLE",
    "MANIMGL_IMPORTED",
    # Classes
    "AnimationGroup",
    "FadeIn",
    "FadeOut",
    "Mobject",
    "Scene",
    "ThreeDScene",
    # Objects
    "logger",
    "config",
]


MANIM_PACKAGE_NAME = "manim"
MANIM_AVAILABLE = find_spec(MANIM_PACKAGE_NAME) is not None
MANIM_IMPORTED = MANIM_PACKAGE_NAME in sys.modules

MANIMGL_PACKAGE_NAME = "manimlib"
MANIMGL_AVAILABLE = find_spec(MANIMGL_PACKAGE_NAME) is not None
MANIMGL_IMPORTED = MANIMGL_PACKAGE_NAME in sys.modules

if MANIM_IMPORTED and MANIMGL_IMPORTED:
    from manim import logger

    logger.warning(
        "Both manim and manimgl are imported, therefore `manim-slide` needs to know which one to use. Please only import one of the two modules so that `manim-slide` knows which one to use. Here, manim is used by default"
    )
    MANIM = True
    MANIMGL = False
elif MANIM_IMPORTED:
    MANIM = True
    MANIMGL = False
elif MANIMGL_IMPORTED:
    MANIM = False
    MANIMGL = True
elif MANIM_AVAILABLE:
    MANIM = True
    MANIMGL = False
elif MANIMGL_AVAILABLE:
    MANIM = False
    MANIMGL = True
else:
    raise ModuleNotFoundError(
        "Either manim (community) or manimgl (3b1b) package must be installed"
    )


if MANIMGL:
    from manimlib import (
        LEFT,
        AnimationGroup,
        FadeIn,
        FadeOut,
        Mobject,
        Scene,
        ThreeDScene,
        config,
    )
    from manimlib.constants import FFMPEG_BIN
    from manimlib.logger import log as logger

else:
    from manim import (
        LEFT,
        AnimationGroup,
        FadeIn,
        FadeOut,
        Mobject,
        Scene,
        ThreeDScene,
        config,
        logger,
    )

    try:  # For manim<v0.16.0.post0
        from manim.constants import FFMPEG_BIN
    except ImportError:
        FFMPEG_BIN = config.ffmpeg_executable
