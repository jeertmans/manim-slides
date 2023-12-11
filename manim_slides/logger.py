"""
Logger utils, mostly copied from Manim Community.

Source code:
https://github.com/ManimCommunity/manim/blob/d5b65b844b8ce8ff5151a2f56f9dc98cebbc1db4/manim/_config/logger_utils.py#L29-L101
"""

import logging

from rich.console import Console
from rich.logging import RichHandler

__all__ = ["logger"]

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
    "Pressed key",
]


def make_logger() -> logging.Logger:
    """Make a logger similar to the one used by Manim."""
    RichHandler.KEYWORDS = HIGHLIGHTED_KEYWORDS
    rich_handler = RichHandler(
        show_time=True,
        console=Console(),
    )
    logger = logging.getLogger("manim-slides")
    logger.setLevel(logging.getLogger("manim").level)
    logger.addHandler(rich_handler)

    if not (libav_logger := logging.getLogger("libav")).hasHandlers():
        libav_logger.addHandler(rich_handler)

    return logger


make_logger()

logger = logging.getLogger("manim-slides")
