"""Qt utils."""

from typing import cast

from qtpy.QtWidgets import QApplication


def qapp() -> QApplication:
    """
    Return a QApplication instance, creating one
    if needed.
    """
    if app := QApplication.instance():
        return cast(QApplication, app)

    return QApplication([])
