import importlib.util
import sys
from itertools import chain, combinations

import pytest
from click.testing import CliRunner
from pytest_missing_modules.plugin import MissingModulesContextGenerator

from manim_slides.__version__ import __version__
from manim_slides.checkhealth import checkhealth

MANIM_NOT_INSTALLED = importlib.util.find_spec("manim") is None
MANIMGL_NOT_INSTALLED = importlib.util.find_spec("manimlib") is None
PYQT6_NOT_INSTALLED = importlib.util.find_spec("PyQt6") is None
PYSIDE6_NOT_INSTALLED = importlib.util.find_spec("PySide6") is None


@pytest.mark.filterwarnings("ignore:Selected binding 'pyqt6' could not be found")
@pytest.mark.parametrize(
    "names",
    list(
        chain.from_iterable(
            combinations(("manim", "manimlib", "PyQt6", "PySide6"), r=r)
            for r in range(0, 5)
        )
    ),
)
def test_checkhealth(
    names: tuple[str, ...], missing_modules: MissingModulesContextGenerator
) -> None:
    runner = CliRunner()

    manim_missing = "manim" in names or MANIM_NOT_INSTALLED
    manimlib_missing = "manimlib" in names or MANIMGL_NOT_INSTALLED
    pyqt6_missing = "PyQt6" in names or PYQT6_NOT_INSTALLED
    pyside6_missing = "PySide6" in names or PYSIDE6_NOT_INSTALLED

    if "qtpy" in sys.modules:
        del sys.modules["qtpy"]  # Avoid using cached module

    with missing_modules(*names):
        if (
            not manimlib_missing
            and not MANIMGL_NOT_INSTALLED
            and sys.version_info < (3, 10)
        ):
            pytest.skip("See https://github.com/3b1b/manim/issues/2263")

        result = runner.invoke(
            checkhealth,
            env={"QT_API": "pyqt6", "FORCE_QT_API": "1"},
        )

        assert result.exit_code == 0
        assert f"Manim Slides version: {__version__}" in result.output
        assert sys.executable in result.output

        if manim_missing:
            assert "manim not found" in result.output
        else:
            assert "manim (version:" in result.output

        if manimlib_missing:
            assert "manimgl not found" in result.output
        else:
            assert "manimgl (version:" in result.output

        if pyqt6_missing and pyside6_missing:
            assert "No Qt API found" in result.output
        elif pyqt6_missing:
            assert "Qt API: pyside6 (version:" in result.output
        else:
            assert "Qt API: pyqt6 (version:" in result.output
