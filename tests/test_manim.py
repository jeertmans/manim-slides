import importlib
import os
import sys

import pytest

import manim_slides.slide as slide

skip_if_py39 = pytest.mark.skipif(
    sys.version_info < (3, 10),
    reason="See https://github.com/3b1b/manim/issues/2263",
)


def assert_import(
    *,
    api_name: str,
    manim: bool,
    manimgl: bool,
) -> None:
    importlib.reload(slide)

    assert slide.API_NAME == api_name
    assert slide.MANIM == manim
    assert slide.MANIMGL == manimgl


@skip_if_py39
def test_force_api() -> None:
    pytest.importorskip("manimlib")
    import manim  # noqa: F401

    if "manimlib" in sys.modules:
        del sys.modules["manimlib"]

    os.environ[slide.MANIM_API] = "manimlib"
    os.environ[slide.FORCE_MANIM_API] = "1"

    assert_import(
        api_name="manimlib",
        manim=False,
        manimgl=True,
    )

    del os.environ[slide.MANIM_API]
    del os.environ[slide.FORCE_MANIM_API]


def test_invalid_api() -> None:
    os.environ[slide.MANIM_API] = "manim_slides"

    with pytest.raises(ImportError):
        assert_import(
            api_name="",
            manim=False,
            manimgl=False,
        )

    del os.environ[slide.MANIM_API]


@skip_if_py39
@pytest.mark.filterwarnings("ignore:assert_import")
def test_manim_and_manimgl_imported() -> None:
    pytest.importorskip("manimlib")
    import manim  # noqa: F401
    import manimlib  # noqa: F401

    assert_import(
        api_name="manim",
        manim=True,
        manimgl=False,
    )


def test_manim_imported() -> None:
    import manim  # noqa: F401

    if "manimlib" in sys.modules:
        del sys.modules["manimlib"]

    assert_import(
        api_name="manim",
        manim=True,
        manimgl=False,
    )


@skip_if_py39
def test_manimgl_imported() -> None:
    pytest.importorskip("manimlib")
    import manimlib  # noqa: F401

    if "manim" in sys.modules:
        del sys.modules["manim"]

    assert_import(
        api_name="manimlib",
        manim=False,
        manimgl=True,
    )


def test_nothing_imported() -> None:
    if "manim" in sys.modules:
        del sys.modules["manim"]

    if "manimlib" in sys.modules:
        del sys.modules["manimlib"]

    assert_import(
        api_name="manim",
        manim=True,
        manimgl=False,
    )
