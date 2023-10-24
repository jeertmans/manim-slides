from pathlib import Path

from click.testing import CliRunner
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMessageBox,
)

from manim_slides.config import Config
from manim_slides.defaults import CONFIG_PATH
from manim_slides.wizard import KeyInput, Wizard, init


class TestKeyInput:
    def test_default_is_none(self, qtbot):
        widget = KeyInput()
        widget.show()
        qtbot.addWidget(widget)
        assert widget.key is None

    def test_send_key(self, qtbot):
        widget = KeyInput()
        widget.show()
        qtbot.addWidget(widget)
        qtbot.keyPress(widget, Qt.Key_Q)
        assert widget.key is Qt.Key_Q.value


class TestWizard:
    def test_close_without_saving(self, qtbot):
        widget = Wizard(Config())
        widget.show()
        qtbot.addWidget(widget)
        widget.button_box.rejected.emit()
        assert widget.closed_without_saving

    def test_save_valid_config(self, qtbot):
        widget = Wizard(Config())
        widget.show()
        qtbot.addWidget(widget)
        widget.button_box.accepted.emit()
        assert not widget.closed_without_saving

    def test_save_invalid_config(self, qtbot, monkeypatch):
        widget = Wizard(Config())
        widget.show()
        qtbot.addWidget(widget)

        def open_dialog(self, button_number, key):
            button = self.buttons[button_number]
            dialog = KeyInput()
            qtbot.addWidget(dialog)
            qtbot.keyPress(dialog, Qt.Key_Q)
            key.set_ids(dialog.key)
            button.setText("Q")
            assert button.text() == "Q"
            dialog.close()

        message_boxes = []

        def exec_patched(self):
            self.show()
            message_boxes.append(self)

        monkeypatch.setattr(QMessageBox, "exec", exec_patched)

        for i, (key, _) in enumerate(widget.config.keys.dict().items()):
            open_dialog(widget, i, getattr(widget.config.keys, key))

        widget.button_box.accepted.emit()
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
        assert Config().dict() == Config.from_file(CONFIG_PATH).dict()


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
        assert Config().dict() == Config.from_file(custom_path).dict()


def test_init_path_exists() -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        assert not CONFIG_PATH.exists()
        results = runner.invoke(
            init,
        )

        assert results.exit_code == 0
        assert CONFIG_PATH.exists()
        assert Config().dict() == Config.from_file(CONFIG_PATH).dict()

        results = runner.invoke(init, input="o")

        assert results.exit_code == 0

        results = runner.invoke(init, input="m")

        assert results.exit_code == 0

        results = runner.invoke(init, input="q")

        assert results.exit_code == 0
