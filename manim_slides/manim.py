import sys
from importlib.util import find_spec

MANIM_PACKAGE_NAME = "manim"
MANIM_AVAILABLE = find_spec(MANIM_PACKAGE_NAME) is not None
MANIM_IMPORTED = MANIM_PACKAGE_NAME in sys.modules

MANIMGL_PACKAGE_NAME = "manimlib"
MANIMGL_AVAILABLE = find_spec(MANIMGL_PACKAGE_NAME) is not None
MANIMGL_IMPORTED = MANIMGL_PACKAGE_NAME in sys.modules

if MANIM_IMPORTED and MANIMGL_IMPORTED:
    from manim import logger

    logger.warn(
        "Both manim and manimgl are installed, therefore `manim-slide` needs to need which one to use. Please only import one of the two modules so that `manim-slide` knows which one to use. Here, manim is used by default"
    )
    MANIM = True
    MANIMGL = False
elif MANIM_AVAILABLE and not MANIMGL_IMPORTED:
    MANIM = True
    MANIMGL = False
elif MANIMGL_AVAILABLE:
    MANIM = False
    MANIMGL = True
else:
    raise ImportError(
        "Either manim (community) or manimgl (3b1b) package must be installed"
    )


FFMPEG_BIN = None

if MANIMGL:
    from manimlib import Scene, ThreeDScene, config
    from manimlib.constants import FFMPEG_BIN
    from manimlib.logger import log as logger

else:
    from manim import Scene, ThreeDScene, config, logger

    try:  # For manim<v0.16.0.post0
        from manim.constants import FFMPEG_BIN as FFMPEG_BIN
    except ImportError:
        FFMPEG_BIN = config.ffmpeg_executable
