import shutil
from enum import EnumMeta
from pathlib import Path

import pytest
from pydantic import ValidationError

from manim_slides.config import PresentationConfig
from manim_slides.convert import (
    PDF,
    AutoAnimateEasing,
    AutoAnimateMatcher,
    AutoPlayMedia,
    AutoSlideMethod,
    BackgroundSize,
    BackgroundTransition,
    ControlsBackArrows,
    ControlsLayout,
    Converter,
    Display,
    HtmlZip,
    JsBool,
    JsFalse,
    JsNull,
    JsTrue,
    KeyboardCondition,
    NavigationMode,
    PowerPoint,
    PreloadIframes,
    RevealJS,
    RevealTheme,
    ShowSlideNumber,
    SlideNumber,
    Transition,
    TransitionSpeed,
    file_to_data_uri,
    get_duration_ms,
)


def test_get_duration_ms(video_file: Path) -> None:
    assert get_duration_ms(video_file) == 2000.0


def test_file_to_data_uri(video_file: Path, video_data_uri_file: Path) -> None:
    assert file_to_data_uri(video_file) == video_data_uri_file.read_text().strip()


@pytest.mark.parametrize(
    ("enum_type",),
    [
        (JsTrue,),
        (JsFalse,),
        (JsBool,),
        (JsNull,),
        (ControlsLayout,),
        (ControlsBackArrows,),
        (SlideNumber,),
        (ShowSlideNumber,),
        (KeyboardCondition,),
        (NavigationMode,),
        (AutoPlayMedia,),
        (PreloadIframes,),
        (AutoAnimateMatcher,),
        (AutoAnimateEasing,),
        (AutoSlideMethod,),
        (Transition,),
        (TransitionSpeed,),
        (BackgroundSize,),
        (BackgroundTransition,),
        (Display,),
        (RevealTheme,),
    ],
)
def test_format_enum(enum_type: EnumMeta) -> None:
    for enum in enum_type:  # type: ignore[var-annotated]
        expected = str(enum)
        got = f"{enum}"

        assert expected == got

        got = "{enum}".format(enum=enum)  # noqa: UP032

        assert expected == got

        got = format(enum, "")

        assert expected == got


@pytest.mark.parametrize(
    ("enum_type",),
    [
        (ControlsLayout,),
        (ControlsBackArrows,),
        (SlideNumber,),
        (ShowSlideNumber,),
        (KeyboardCondition,),
        (NavigationMode,),
        (AutoPlayMedia,),
        (PreloadIframes,),
        (AutoAnimateMatcher,),
        (AutoAnimateEasing,),
        (AutoSlideMethod,),
        (Transition,),
        (TransitionSpeed,),
        (BackgroundSize,),
        (BackgroundTransition,),
        (Display,),
    ],
)
def test_quoted_enum(enum_type: EnumMeta) -> None:
    for enum in enum_type:  # type: ignore[var-annotated]
        if enum in ["true", "false", "null"]:
            continue

        expected = "'" + enum.value + "'"
        got = str(enum)

        assert expected == got


@pytest.mark.parametrize(
    ("enum_type",),
    [
        (JsTrue,),
        (JsFalse,),
        (JsBool,),
        (JsNull,),
        (RevealTheme,),
    ],
)
def test_unquoted_enum(enum_type: EnumMeta) -> None:
    for enum in enum_type:  # type: ignore[var-annotated]
        expected = enum.value
        got = str(enum)

        assert expected == got


class TestConverter:
    @pytest.mark.parametrize(
        ("name", "converter"),
        [("html", RevealJS), ("pdf", PDF), ("pptx", PowerPoint), ("zip", HtmlZip)],
    )
    def test_from_string(self, name: str, converter: type) -> None:
        assert Converter.from_string(name) == converter

    def test_revealjs_converter(
        self, tmp_path: Path, presentation_config: PresentationConfig
    ) -> None:
        out_file = tmp_path / "slides.html"
        RevealJS(presentation_configs=[presentation_config]).convert_to(out_file)
        assert out_file.exists()
        assert Path(tmp_path / "slides_assets").is_dir()
        file_contents = out_file.read_text()
        assert "manim" in file_contents.casefold()

    def test_htmlzip_converter(
        self, tmp_path: Path, presentation_config: PresentationConfig
    ) -> None:
        archive = tmp_path / "got.zip"
        expected = tmp_path / "expected.html"
        got = tmp_path / "got.html"

        HtmlZip(presentation_configs=[presentation_config]).convert_to(archive)
        RevealJS(presentation_configs=[presentation_config]).convert_to(expected)

        shutil.unpack_archive(str(archive), extract_dir=tmp_path)

        assert archive.exists()
        assert got.exists()
        assert expected.exists()

        assert got.read_text() == expected.read_text().replace(
            "expected_assets", "got_assets"
        )

    @pytest.mark.parametrize("num_presentation_configs", (1, 2))
    def test_revealjs_multiple_scenes_converter(
        self,
        tmp_path: Path,
        presentation_config: PresentationConfig,
        num_presentation_configs: int,
    ) -> None:
        out_file = tmp_path / "slides.html"
        RevealJS(
            presentation_configs=[
                presentation_config for _ in range(num_presentation_configs)
            ]
        ).convert_to(out_file)
        assert out_file.exists()
        assets_dir = Path(tmp_path / "slides_assets")
        assert assets_dir.is_dir()

        got = sum(1 for _ in assets_dir.iterdir())
        expected = num_presentation_configs * len(presentation_config.slides)

        assert got == expected

    @pytest.mark.parametrize("frame_index", ("first", "last"))
    def test_pdf_converter(
        self, frame_index: str, tmp_path: Path, presentation_config: PresentationConfig
    ) -> None:
        out_file = tmp_path / "slides.pdf"
        PDF(
            presentation_configs=[presentation_config], frame_index=frame_index
        ).convert_to(out_file)
        assert out_file.exists()

    def test_converter_no_presentation_config(self) -> None:
        with pytest.raises(ValidationError):
            Converter(presentation_configs=[])

    def test_pptx_converter(
        self, tmp_path: Path, presentation_config: PresentationConfig
    ) -> None:
        out_file = tmp_path / "slides.pptx"
        PowerPoint(presentation_configs=[presentation_config]).convert_to(out_file)
        assert out_file.exists()
