import os
import sys

import click
import cv2
import numpy as np

from .commons import config_options
from .config import Config
from .defaults import CONFIG_PATH, FONT_ARGS

WINDOW_NAME = "Manim Slides Configuration Wizard"
WINDOW_SIZE = (120, 620)


def center_text_horizontally(text, window_size, font_args) -> int:
    """Returns centered position for text to be displayed in current window."""
    _, width = window_size
    font, scale, _, thickness, _ = font_args
    (size_in_pixels, _), _ = cv2.getTextSize(text, font, scale, thickness)
    return (width - size_in_pixels) // 2


def prompt(question: str) -> int:
    """Diplays some question in current window and waits for key press."""
    display = np.zeros(WINDOW_SIZE, np.uint8)

    text = "* Manim Slides Wizard *"
    text_org = center_text_horizontally(text, WINDOW_SIZE, FONT_ARGS), 33
    question_org = center_text_horizontally(question, WINDOW_SIZE, FONT_ARGS), 85

    cv2.putText(display, "* Manim Slides Wizard *", text_org, *FONT_ARGS)
    cv2.putText(display, question, question_org, *FONT_ARGS)

    cv2.imshow(WINDOW_NAME, display)
    return cv2.waitKeyEx(-1)


@click.command()
@config_options
@click.help_option("-h", "--help")
def wizard(config_path, force, merge):
    """Launch configuration wizard."""
    return _init(config_path, force, merge, skip_interactive=False)


@click.command()
@config_options
@click.help_option("-h", "--help")
def init(config_path, force, merge, skip_interactive=False):
    """Initialize a new default configuration file."""
    return _init(config_path, force, merge, skip_interactive=True)


def _init(config_path, force, merge, skip_interactive=False):
    """Actual initialization code for configuration file, with optional interactive mode."""

    if os.path.exists(config_path):
        click.secho(f"The `{CONFIG_PATH}` configuration file exists")

        if not force and not merge:
            choice = click.prompt(
                "Do you want to continue and (o)verwrite / (m)erge it, or (q)uit?",
                type=click.Choice(["o", "m", "q"], case_sensitive=False),
            )

            force = choice == "o"
            merge = choice == "m"

        if force:
            click.secho("Overwriting.")
        elif merge:
            click.secho("Merging.")
        else:
            click.secho("Exiting.")
            sys.exit(0)

    config = Config()

    if not skip_interactive:

        cv2.namedWindow(
            WINDOW_NAME,
            cv2.WINDOW_GUI_NORMAL | cv2.WINDOW_FREERATIO | cv2.WINDOW_AUTOSIZE,
        )

        prompt("Press any key to continue")

        for _, key in config:
            key.ids = [prompt(f"Press the {key.name} key")]

    if merge:
        config = Config.parse_file(config_path).merge_with(config)

    with open(config_path, "w") as config_file:
        config_file.write(config.json(indent=2))

    click.echo(f"Configuration file successfully save to `{config_path}`")
