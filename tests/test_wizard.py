from pathlib import Path

from click.testing import CliRunner
from pytest import MonkeyPatch
from pytestqt.qtbot import QtBot
from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QApplication,
    QMessageBox,
)

from manim_slides.config import Config, Key
from manim_slides.defaults import CONFIG_PATH
from manim_slides.wizard import init, wizard
from manim_slides.wizard.wizard import KeyInput, Wizard


class TestKeyInput:
    def test_default_is_none(self, qtbot: QtBot) -> None:
        widget = KeyInput()
        widget.show()
        qtbot.addWidget(widget)
        assert widget.key is None

    def test_send_key(self, qtbot: QtBot) -> None:
        widget = KeyInput()
        widget.show()
        qtbot.addWidget(widget)
        qtbot.keyPress(widget, Qt.Key_Q)
        assert widget.key is Qt.Key_Q.value


class TestWizard:
    def test_close_without_saving(self, qtbot: QtBot) -> None:
        wizard = Wizard(Config())
        wizard.show()
        qtbot.addWidget(wizard)
        wizard.button_box.rejected.emit()
        assert wizard.closed_without_saving

    def test_save_valid_config(self, qtbot: QtBot) -> None:
        widget = Wizard(Config())
        widget.show()
        qtbot.addWidget(widget)
        widget.button_box.accepted.emit()
        assert not widget.closed_without_saving

    def test_save_invalid_config(self, qtbot: QtBot, monkeypatch: MonkeyPatch) -> None:
        wizard = Wizard(Config())
        wizard.show()
        qtbot.addWidget(wizard)

        def open_dialog(button_number: int, key: Key) -> None:
            button = wizard.buttons[button_number]
            dialog = KeyInput()
            qtbot.addWidget(dialog)
            qtbot.keyPress(dialog, Qt.Key_Q)
            assert dialog.key is not None
            key.set_ids(dialog.key)
            button.setText("Q")
            assert button.text() == "Q"
            dialog.close()

        message_boxes = []

        def exec_patched(self: QMessageBox) -> None:
            self.show()
            message_boxes.append(self)

        monkeypatch.setattr(QMessageBox, "exec", exec_patched)

        for i, (key, _) in enumerate(wizard.config.keys.model_dump().items()):
            open_dialog(i, getattr(wizard.config.keys, key))

        wizard.button_box.accepted.emit()
        message_box = message_boxes.pop()
        qtbot.addWidget(message_box)
        assert message_box.isVisible()


def test_init() -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        assert not CONFIG_PATH.exists()
        results = runner.invoke(
            init,
        )

        assert results.exit_code == 0
        assert CONFIG_PATH.exists()
        assert Config().model_dump() == Config.from_file(CONFIG_PATH).model_dump()


def test_init_custom_path() -> None:
    runner = CliRunner()
    custom_path = Path("config.toml")

    with runner.isolated_filesystem():
        assert not custom_path.exists()
        results = runner.invoke(
            init,
            ["--config", str(custom_path)],
        )

        assert results.exit_code == 0
        assert not CONFIG_PATH.exists()
        assert custom_path.exists()
        assert Config().model_dump() == Config.from_file(custom_path).model_dump()


def test_init_path_exists() -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        assert not CONFIG_PATH.exists()
        results = runner.invoke(
            init,
        )

        assert results.exit_code == 0
        assert CONFIG_PATH.exists()
        assert Config().model_dump() == Config.from_file(CONFIG_PATH).model_dump()

        results = runner.invoke(init, input="o")

        assert results.exit_code == 0

        results = runner.invoke(init, input="m")

        assert results.exit_code == 0

        results = runner.invoke(init, input="q")

        assert results.exit_code == 0


def test_wizard(monkeypatch: MonkeyPatch) -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        assert not CONFIG_PATH.exists()

        def show(self: Wizard) -> None:
            self.button_box.accepted.emit()

        def exec_patched(self: QApplication) -> None:
            pass

        monkeypatch.setattr(Wizard, "show", show)
        monkeypatch.setattr(QApplication, "exec", exec_patched)

        results = runner.invoke(
            wizard,
        )

        assert results.exit_code == 0
        assert CONFIG_PATH.exists()
        assert Config().model_dump() == Config.from_file(CONFIG_PATH).model_dump()


def test_wizard_closed_without_saving(monkeypatch: MonkeyPatch) -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        assert not CONFIG_PATH.exists()

        def show(self: Wizard) -> None:
            self.button_box.rejected.emit()

        def exec_patched(self: QApplication) -> None:
            pass

        monkeypatch.setattr(Wizard, "show", show)
        monkeypatch.setattr(QApplication, "exec", exec_patched)

        results = runner.invoke(
            wizard,
        )

        assert results.exit_code == 0
        assert not CONFIG_PATH.exists()
