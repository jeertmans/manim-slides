"""Qt utils."""

from qtpy.QtWidgets import QApplication


def qapp() -> QApplication:
    """
    Return a QApplication instance, creating one
    if needed.
    """
    if app := QApplication.instance():
        return app

    return QApplication([])
