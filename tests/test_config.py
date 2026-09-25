from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from manim_slides.config import (
    BaseSlideConfig,
    CommandDefaults,
    Config,
    Key,
    PresentationConfig,
    SlideType,
)


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


class TestConfig:
    def test_defaults_are_empty_by_default(self) -> None:
        config = Config()

        assert config.defaults.root == {}

    def test_valid_defaults(self) -> None:
        config = Config.model_validate(
            {
                "defaults": {
                    "present": {"full_screen": True, "folder": "my_slides"},
                    "convert": {"to": "pdf", "one_file": True},
                }
            }
        )

        assert config.defaults.root == {
            "present": {"full_screen": True, "folder": "my_slides"},
            "convert": {"to": "pdf", "one_file": True},
        }

    def test_defaults_roundtrip_toml(self, tmp_path: Path) -> None:
        config = Config.model_validate(
            {"defaults": {"present": {"full_screen": True, "folder": "my_slides"}}}
        )

        config_file = tmp_path / "config.toml"
        config.to_file(config_file)

        assert Config.from_file(config_file) == config

    @pytest.mark.parametrize(
        ("defaults", "expected_error"),
        [
            ({"present": 1}, "Invalid defaults for command 'present'"),
            ({"present": "text"}, "Invalid defaults for command 'present'"),
            ({"present": {"key": {"nested": "table"}}}, "nested tables"),
            ({"present": {"key": [["nested", "list"]]}}, "lists must only contain"),
        ],
    )
    def test_invalid_defaults(self, defaults: Any, expected_error: str) -> None:
        with pytest.raises(ValidationError, match=expected_error):
            _ = Config.model_validate({"defaults": defaults})

    def test_merge_defaults(self) -> None:
        base = Config.model_validate(
            {"defaults": {"present": {"full_screen": True, "skip_all": False}}}
        )
        other = Config.model_validate(
            {"defaults": {"present": {"full_screen": False, "folder": "x"}}}
        )

        merged = base.merge_with(other)

        assert merged.defaults.root == {
            "present": {"full_screen": False, "skip_all": False, "folder": "x"}
        }

    def test_merge_defaults_new_command(self) -> None:
        base = Config.model_validate({"defaults": {"present": {"full_screen": True}}})
        other = Config.model_validate({"defaults": {"convert": {"to": "pdf"}}})

        merged = base.merge_with(other)

        assert merged.defaults.root == {
            "present": {"full_screen": True},
            "convert": {"to": "pdf"},
        }


class TestCommandDefaults:
    def test_merge_with_takes_precedence(self) -> None:
        base = CommandDefaults.model_validate({"present": {"a": 1, "b": 2}})
        other = CommandDefaults.model_validate({"present": {"b": 3, "c": 4}})

        assert base.merge_with(other).root == {"present": {"a": 1, "b": 3, "c": 4}}

    def test_merge_with_empty(self) -> None:
        base = CommandDefaults.model_validate({"present": {"a": 1}})
        other = CommandDefaults.model_validate({})

        assert base.merge_with(other).root == {"present": {"a": 1}}
        assert other.merge_with(base).root == {"present": {"a": 1}}


class TestPresentationConfig:
    def test_validate(self, presentation_config: PresentationConfig) -> None:
        obj = presentation_config.model_dump()
        _ = PresentationConfig.model_validate(obj)

    def test_bump_to_json(self, presentation_config: PresentationConfig) -> None:
        _ = presentation_config.model_dump_json(indent=2)

    def test_empty_presentation_config(self) -> None:
        with pytest.raises(ValidationError):
            _ = PresentationConfig(slides=[])


class TestBaseSlideConfig:
    @pytest.mark.parametrize(
        ("src", "expected_type"),
        [
            ("test.png", SlideType.Image),
            ("test.mp4", SlideType.Video),
            (None, SlideType.Video),
        ],
    )
    def test_determine_slide_type(
        self, src: Any, expected_type: Any, tmp_path: Path
    ) -> None:
        if src is not None:
            src = tmp_path / src
            src.touch()  # create the file
        obj = BaseSlideConfig(src=src)
        if obj.type != expected_type:
            raise AssertionError(f"Expected {expected_type}, got {obj.type}")
