import os
import sys
from functools import partial
from typing import Any

import click
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .commons import config_options, verbosity_option
from .config import Config, Key
from .defaults import CONFIG_PATH
from .manim import logger

WINDOW_NAME: str = "Configuration Wizard"

keymap = {}
for key, value in vars(Qt).items():
    if isinstance(value, Qt.Key):
        keymap[value] = key.partition("_")[2]


class KeyInput(QDialog):
    def __init__(self) -> None:
        super().__init__()
        self.key = None

        self.layout = QVBoxLayout()

        self.setWindowTitle("Keyboard Input")
        self.label = QLabel("Press any key to register it")
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)

    def keyPressEvent(self, event: Any) -> None:
        self.key = event.key()
        self.deleteLater()
        event.accept()


class Wizard(QWidget):
    def __init__(self, config: Config):

        super().__init__()

        self.setWindowTitle(WINDOW_NAME)
        self.config = config

        QBtn = QDialogButtonBox.Save | QDialogButtonBox.Cancel

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.saveConfig)
        self.buttonBox.rejected.connect(self.closeWithoutSaving)

        self.buttons = []

        self.layout = QGridLayout()

        for i, (key, value) in enumerate(self.config.dict().items()):
            # Create label for key name information
            label = QLabel()
            key_info = value["name"] or key
            label.setText(key_info)
            self.layout.addWidget(label, i, 0)

            # Create button that will pop-up a dialog and ask to input a new key
            value = value["ids"].pop()
            button = QPushButton(keymap[value])
            button.setToolTip(
                f"Click to modify the key associated to action {key_info}"
            )
            self.buttons.append(button)
            button.clicked.connect(
                partial(self.openDialog, i, getattr(self.config, key))
            )
            self.layout.addWidget(button, i, 1)

        self.layout.addWidget(self.buttonBox, len(self.buttons), 1)

        self.setLayout(self.layout)

    def closeWithoutSaving(self) -> None:
        logger.debug("Closing configuration wizard without saving")
        self.deleteLater()
        sys.exit(0)

    def closeEvent(self, event: Any) -> None:
        self.closeWithoutSaving()
        event.accept()

    def saveConfig(self) -> None:
        try:
            Config.parse_obj(self.config.dict())
        except ValueError:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Error")
            msg.setInformativeText(
                "Two or more actions share a common key: make sure actions have distinct key codes."
            )
            msg.setWindowTitle("Error: duplicated keys")
            msg.exec_()
            return

        self.deleteLater()

    def openDialog(self, button_number: int, key: Key) -> None:
        button = self.buttons[button_number]
        dialog = KeyInput()
        dialog.exec_()
        if dialog.key is not None:
            key_name = keymap[dialog.key]
            key.set_ids(dialog.key)
            button.setText(key_name)


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

        if not force and not merge:
            logger.debug("Exiting without doing anything")
            sys.exit(0)

    config = Config()

    if force:
        logger.debug(f"Overwriting `{config_path}` if exists")
    elif merge:
        logger.debug("Merging new config into `{config_path}`")

    if not skip_interactive:
        if os.path.exists(config_path):
            config = Config.parse_file(config_path)

        app = QApplication(sys.argv)
        app.setApplicationName("Manim Slides Wizard")
        window = Wizard(config)
        window.show()
        app.exec()

        config = window.config

    if merge:
        config = Config.parse_file(config_path).merge_with(config)

    with open(config_path, "w") as config_file:
        config_file.write(config.json(indent=2))

    click.secho(f"Configuration file successfully saved to `{config_path}`")
