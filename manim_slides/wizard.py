import sys
from functools import partial
from pathlib import Path
from typing import Any

import click
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QKeyEvent
from PySide6.QtWidgets import (
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
from .logger import logger
from .qt_utils import qapp
from .resources import *  # noqa: F403

WINDOW_NAME: str = "Configuration Wizard"

keymap = {}
for key in Qt.Key:
    keymap[key.value] = key.name.partition("_")[2]


class KeyInput(QDialog):  # type: ignore
    def __init__(self) -> None:
        super().__init__()
        self.key = None

        self.layout = QVBoxLayout()

        self.setWindowTitle("Keyboard Input")
        self.label = QLabel("Press any key to register it")
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        self.key = event.key()
        self.deleteLater()
        event.accept()


class Wizard(QWidget):  # type: ignore
    def __init__(self, config: Config):
        super().__init__()

        self.setWindowTitle(WINDOW_NAME)
        self.config = config
        self.icon = QIcon(":/icon.png")
        self.setWindowIcon(self.icon)
        self.closed_without_saving = False

        button = QDialogButtonBox.Save | QDialogButtonBox.Cancel

        self.button_box = QDialogButtonBox(button)
        self.button_box.accepted.connect(self.save_config)
        self.button_box.rejected.connect(self.close_without_saving)

        self.buttons = []

        self.layout = QGridLayout()

        for i, (key, value) in enumerate(self.config.keys.dict().items()):
            # Create label for key name information
            label = QLabel()
            key_info = value["name"] or key
            label.setText(key_info.title())
            self.layout.addWidget(label, i, 0)

            # Create button that will pop-up a dialog and ask to input a new key
            value = value["ids"].pop()
            button = QPushButton(keymap[value])
            button.setToolTip(
                f"Click to modify the key associated to action {key_info}"
            )
            self.buttons.append(button)
            button.clicked.connect(
                partial(self.open_dialog, i, getattr(self.config.keys, key))
            )
            self.layout.addWidget(button, i, 1)

        self.layout.addWidget(self.button_box, len(self.buttons), 1)

        self.setLayout(self.layout)

    def close_without_saving(self) -> None:
        logger.debug("Closing configuration wizard without saving")
        self.closed_without_saving = True
        self.deleteLater()

    def closeEvent(self, event: Any) -> None:  # noqa: N802
        self.close_without_saving()
        event.accept()

    def save_config(self) -> None:
        try:
            Config.model_validate(self.config.dict())
        except ValueError:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Error")
            msg.setInformativeText(
                "Two or more actions share a common key: make sure actions have distinct key codes."
            )
            msg.setWindowTitle("Error: duplicated keys")
            msg.exec()
            return

        self.deleteLater()

    def open_dialog(self, button_number: int, key: Key) -> None:
        button = self.buttons[button_number]
        dialog = KeyInput()
        dialog.exec()
        if dialog.key is not None:
            key_name = keymap[dialog.key]
            key.set_ids(dialog.key)
            button.setText(key_name)


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
