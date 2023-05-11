"""
Logger utils, mostly copied from Manim Community:
https://github.com/ManimCommunity/manim/blob/d5b65b844b8ce8ff5151a2f56f9dc98cebbc1db4/manim/_config/logger_utils.py#L29-L101
"""

import logging

from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme

__all__ = ["logger", "make_logger"]

HIGHLIGHTED_KEYWORDS = [  # these keywords are highlighted specially
    "Played",
    "animations",
    "scene",
    "Reading",
    "Writing",
    "script",
    "arguments",
    "Invalid",
    "Aborting",
    "module",
    "File",
    "Rendering",
    "Rendered",
]


def make_logger() -> logging.Logger:
    """
    Make a logger similar to the one used by Manim.
    """
    RichHandler.KEYWORDS = HIGHLIGHTED_KEYWORDS
    rich_handler = RichHandler(
        show_time=True,
        console=Console(theme=Theme({"logging.level.perf": "magenta"})),
    )
    logging.addLevelName(5, "PERF")
    logger = logging.getLogger("manim-slides")
    logger.addHandler(rich_handler)

    return logger


logger = logging.getLogger("manim-slides")
