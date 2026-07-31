from functools import partial
from typing import Any

from qtpy.QtCore import Qt
from qtpy.QtGui import QIcon, QKeyEvent
from qtpy.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..config import Config, Key
from ..logger import logger
from ..resources import *

WINDOW_NAME: str = "Configuration Wizard"

keymap = {}
for key in Qt.Key:
    keymap[key.value] = key.name.partition("_")[2]


class KeyInput(QDialog):
    def __init__(self) -> None:
        super().__init__()
        self.key = None

        self._layout = QVBoxLayout()

        self.setWindowTitle("Keyboard Input")
        self.label = QLabel("Press any key to register it")
        self._layout.addWidget(self.label)
        self.setLayout(self._layout)

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        self.key = event.key()
        self.deleteLater()
        event.accept()


class Wizard(QWidget):
    def __init__(self, config: Config):
        super().__init__()

        self.setWindowTitle(WINDOW_NAME)
        self.config = config
        self.icon = QIcon(":/icon.png")
        self.setWindowIcon(self.icon)
        self.closed_without_saving = False

        button = (
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )

        self.button_box = QDialogButtonBox(button)
        self.button_box.accepted.connect(self.save_config)
        self.button_box.rejected.connect(self.close_without_saving)

        self.buttons = []

        self._layout = QGridLayout()

        for i, (key, value) in enumerate(self.config.keys.model_dump().items()):
            # Create label for key name information
            label = QLabel()
            key_info = value["name"] or key
            label.setText(key_info.title())
            self._layout.addWidget(label, i, 0)

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
            self._layout.addWidget(button, i, 1)

        self._layout.addWidget(self.button_box, len(self.buttons), 1)

        self.setLayout(self._layout)

    def close_without_saving(self) -> None:
        logger.debug("Closing configuration wizard without saving")
        self.closed_without_saving = True
        self.deleteLater()

    def closeEvent(self, event: Any) -> None:  # noqa: N802
        self.close_without_saving()
        event.accept()

    def save_config(self) -> None:
        try:
            Config.model_validate(self.config.model_dump())
        except ValueError:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
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
