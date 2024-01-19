import sys
from pathlib import Path

import click

from ..commons import config_options, verbosity_option
from ..config import Config
from ..defaults import CONFIG_PATH
from ..logger import logger


@click.command()
@config_options
@click.help_option("-h", "--help")
@verbosity_option
def wizard(config_path: Path, force: bool, merge: bool) -> None:
    """Launch configuration wizard."""
    return _init(config_path, force, merge, skip_interactive=False)


@click.command()
@config_options
@click.help_option("-h", "--help")
@verbosity_option
def init(
    config_path: Path, force: bool, merge: bool, skip_interactive: bool = False
) -> None:
    """Initialize a new default configuration file."""
    return _init(config_path, force, merge, skip_interactive=True)


def _init(
    config_path: Path, force: bool, merge: bool, skip_interactive: bool = False
) -> None:
    """
    Actual initialization code for configuration file, with optional interactive
    mode.
    """
    if config_path.exists():
        click.secho(f"The `{CONFIG_PATH}` configuration file exists")

        if not force and not merge:
            choice = click.prompt(
                "Do you want to continue and (o)verwrite / (m)erge it, or (q)uit?",
                type=click.Choice(["o", "m", "q"], case_sensitive=False),
            )

            force = choice == "o"
            merge = choice == "m"

        if not force and not merge:
            logger.debug("Exiting without doing anything")
            sys.exit(0)

    config = Config()

    if force:
        logger.debug(f"Overwriting `{config_path}` if exists")
    elif merge:
        logger.debug("Merging new config into `{config_path}`")

    if not skip_interactive:
        if config_path.exists():
            config = Config.from_file(config_path)

        from ..qt_utils import qapp
        from .wizard import Wizard

        app = qapp()
        app.setApplicationName("Manim Slides Wizard")
        window = Wizard(config)
        window.show()
        app.exec()

        if window.closed_without_saving:
            sys.exit(0)

        config = window.config

    if merge:
        config = Config.from_file(config_path).merge_with(config)

    config.to_file(config_path)

    click.secho(f"Configuration file successfully saved to `{config_path}`")
