import os
import sys

import click
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget

from .commons import config_options, verbosity_option
from .config import Config
from .defaults import CONFIG_PATH

WINDOW_NAME = "Manim Slides Configuration Wizard"
WINDOW_SIZE = (120, 620)


class KeyInput(QWidget):
    pass


class Wizard(QWidget):
    def __init__(self, config):

        super().__init__()

        self.setWindowTitle(WINDOW_NAME)
        self.resize(*WINDOW_SIZE)

        self.setLayout(config.into_qt_widget())


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
@verbosity_option
def wizard(config_path, force, merge):
    """Launch configuration wizard."""
    return _init(config_path, force, merge, skip_interactive=False)


@click.command()
@config_options
@click.help_option("-h", "--help")
@verbosity_option
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

    app = QApplication(sys.argv)
    print(config.into_qt_widget())
    window = Wizard(config)
    window.show()
    app.exec()

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
