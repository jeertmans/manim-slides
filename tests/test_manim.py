import importlib
import sys
from contextlib import contextmanager
from importlib.abc import MetaPathFinder
from importlib.machinery import ModuleSpec
from types import ModuleType
from typing import Iterator, Optional, Sequence

import pytest

import manim_slides.manim as msm


@contextmanager
def suppress_module_finder() -> Iterator[None]:
    meta_path = sys.meta_path
    try:

        class PathFinder(MetaPathFinder):
            @classmethod
            def find_spec(
                cls,
                fullname: str,
                path: Optional[Sequence[str]],
                target: Optional[ModuleType] = None,
            ) -> Optional[ModuleSpec]:
                if fullname in ["manim", "manimlib"]:
                    return None

                for finder in meta_path:
                    spec = finder.find_spec(fullname, path, target=target)
                    if spec is not None:
                        return spec

                return None

        sys.meta_path = [PathFinder]
        yield
    finally:
        sys.meta_path = meta_path


def assert_import(
    *,
    manim: bool,
    manim_available: bool,
    manim_imported: bool,
    manimgl: bool,
    manimgl_available: bool,
    manimgl_imported: bool,
) -> None:
    importlib.reload(msm)

    assert msm.MANIM == manim
    assert msm.MANIM_AVAILABLE == manim_available
    assert msm.MANIM_IMPORTED == manim_imported
    assert msm.MANIMGL == manimgl
    assert msm.MANIMGL_AVAILABLE == manim_available
    assert msm.MANIMGL_IMPORTED == manimgl_imported


@pytest.mark.filterwarnings("ignore:assert_import")
def test_manim_and_manimgl_imported() -> None:
    import manim  # noqa: F401
    import manimlib  # noqa: F401

    assert_import(
        manim=True,
        manim_available=True,
        manim_imported=True,
        manimgl=False,
        manimgl_available=True,
        manimgl_imported=True,
    )


def test_manim_imported() -> None:
    import manim  # noqa: F401

    if "manimlib" in sys.modules:
        del sys.modules["manimlib"]

    assert_import(
        manim=True,
        manim_available=True,
        manim_imported=True,
        manimgl=False,
        manimgl_available=True,
        manimgl_imported=False,
    )


def test_manimgl_imported() -> None:
    import manimlib  # noqa: F401

    if "manim" in sys.modules:
        del sys.modules["manim"]

    assert_import(
        manim=False,
        manim_available=True,
        manim_imported=False,
        manimgl=True,
        manimgl_available=True,
        manimgl_imported=True,
    )


def test_nothing_imported() -> None:
    if "manim" in sys.modules:
        del sys.modules["manim"]

    if "manimlib" in sys.modules:
        del sys.modules["manimlib"]

    assert_import(
        manim=True,
        manim_available=True,
        manim_imported=False,
        manimgl=False,
        manimgl_available=True,
        manimgl_imported=False,
    )


def test_no_package_available() -> None:
    with suppress_module_finder():
        if "manim" in sys.modules:
            del sys.modules["manim"]

        if "manimlib" in sys.modules:
            del sys.modules["manimlib"]

        with pytest.raises(ModuleNotFoundError):
            # Actual values are not important
            assert_import(
                manim=False,
                manim_available=False,
                manim_imported=False,
                manimgl=False,
                manimgl_available=False,
                manimgl_imported=False,
            )
