import os
import sys

import click
import cv2
import numpy as np

from .commons import config_options
from .config import Config
from .defaults import CONFIG_PATH


def prompt(question: str) -> int:
    font_args = (cv2.FONT_HERSHEY_SIMPLEX, 0.7, 255)
    display = np.zeros((130, 420), np.uint8)

    cv2.putText(display, "* Manim Slides Wizard *", (70, 33), *font_args)
    cv2.putText(display, question, (30, 85), *font_args)

    cv2.imshow("Manim Slides Configuration Wizard", display)
    return cv2.waitKeyEx(-1)


@click.command()
@config_options
def wizard(config_path, force, merge):
    """Launch configuration wizard."""
    return _init(config_path, force, merge, skip_interactive=False)


@click.command()
@config_options
def init(config_path, force, merge, skip_interactive=False):
    """Initialize a new default configuration file."""
    return _init(config_path, force, merge, skip_interactive=True)


def _init(config_path, force, merge, skip_interactive=False):

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

        prompt("Press any key to continue")

        for _, key in config:
            key.ids = [prompt(f"Press the {key.name} key")]

    if merge:
        config = Config.parse_file(config_path).merge_with(config)

    with open(config_path, "w") as config_file:
        config_file.write(config.json(indent=4))

    click.echo(f"Configuration file successfully save to `{config_path}`")
