from qtpy.QtWidgets import QApplication

from manim_slides.qt_utils import qapp


def test_qapp() -> None:
    assert isinstance(qapp(), QApplication)


def test_duplicated_qapp() -> None:
    app1 = qapp()
    app2 = qapp()

    assert app1 == app2
