"""Qt utils."""

from PySide6.QtWidgets import QApplication


def qapp() -> QApplication:
    """
    Return a QApplication instance, creating one
    if needed.
    """
    if app := QApplication.instance():
        return app

    return QApplication([])
