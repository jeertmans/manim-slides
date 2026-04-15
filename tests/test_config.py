from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from manim_slides.config import BaseSlideConfig, Key, PresentationConfig, SlideType


class TestKey:
    @pytest.mark.parametrize(("ids", "name"), [([1], None), ([1], "some key name")])
    def test_valid_keys(self, ids: Any, name: Any) -> None:
        _ = Key(ids=ids, name=name)

    @pytest.mark.parametrize(
        ("ids", "name"), [([], None), ([-1], None), ([1], {"an": " invalid name"})]
    )
    def test_invalid_keys(self, ids: Any, name: Any) -> None:
        with pytest.raises(ValidationError):
            _ = Key(ids=ids, name=name)


class TestPresentationConfig:
    def test_validate(self, presentation_config: PresentationConfig) -> None:
        obj = presentation_config.model_dump()
        _ = PresentationConfig.model_validate(obj)

    def test_bump_to_json(self, presentation_config: PresentationConfig) -> None:
        _ = presentation_config.model_dump_json(indent=2)

    def test_empty_presentation_config(self) -> None:
        with pytest.raises(ValidationError):
            _ = PresentationConfig(slides=[], files=[])


class TestBaseSlideConfig:
    @pytest.mark.parametrize(
        ("src", "expected_type"),
        [
            ("test.png", SlideType.Image),
            ("test.mp4", SlideType.Video),
            (None, SlideType.Video),
        ],
    )
    def test_determine_slide_type(self, src: Any, expected_type: Any, tmp_path: Path) -> None:
        if src is not None:
            src = tmp_path / src
            src.touch()  # create the file
        obj = BaseSlideConfig(src=src)
        if obj.type != expected_type:
            raise AssertionError(f"Expected {expected_type}, got {obj.type}")
