"""Tests for config file discovery and command defaults."""

import sys
from pathlib import Path
from unittest import mock

import pytest
import rtoml

# Mock qtpy before importing any manim_slides.config classes,
# since Keys defaults depend on Qt key constants.
_qt_mock = mock.MagicMock()
_qt_mock.QtCore.Qt.Key_Right = 0x01000014
_qt_mock.QtCore.Qt.Key_Left = 0x01000012
_qt_mock.QtCore.Qt.Key_Up = 0x01000013
_qt_mock.QtCore.Qt.Key_Down = 0x01000015
_qt_mock.QtCore.Qt.Key_Space = 0x20
_qt_mock.QtCore.Qt.Key_Q = 0x51
_qt_mock.QtCore.Qt.Key_V = 0x56
_qt_mock.QtCore.Qt.Key_R = 0x52
_qt_mock.QtCore.Qt.Key_Return = 0x01000004
_qt_mock.QtCore.Qt.Key_Backspace = 0x01000003
_qt_mock.QtCore.Qt.Key_F5 = 0x01000034
sys.modules.setdefault("qtpy", _qt_mock)
sys.modules.setdefault("qtpy.QtCore", _qt_mock.QtCore)

from manim_slides.config import (  # noqa: E402
    Config,
    find_config_files,
    load_merged_config,
)


class TestConfigWithCommands:
    """Test Config model with command defaults."""

    def test_empty_commands(self) -> None:
        config = Config()
        assert config.commands == {}
        assert config.get_default_map() == {}

    def test_commands_from_dict(self) -> None:
        config = Config(
            commands={
                "present": {"full_screen": True, "hide_mouse": True},
                "convert": {"one_file": True},
            }
        )
        assert config.commands["present"]["full_screen"] is True
        assert config.commands["convert"]["one_file"] is True

    def test_get_default_map(self) -> None:
        config = Config(
            commands={
                "present": {"full_screen": True},
                "convert": {"one_file": True, "offline": True},
            }
        )
        default_map = config.get_default_map()
        assert default_map == {
            "present": {"full_screen": True},
            "convert": {"one_file": True, "offline": True},
        }

    def test_from_toml_with_commands(self, tmp_path: Path) -> None:
        config_data: dict[str, Any] = {
            "keys": {},
            "commands": {
                "present": {"full_screen": True},
                "convert": {"one_file": True},
            },
        }
        config_file = tmp_path / "config.toml"
        rtoml.dump(config_data, config_file, pretty=True)

        config = Config.from_file(config_file)
        assert config.commands["present"]["full_screen"] is True
        assert config.commands["convert"]["one_file"] is True

    def test_from_toml_without_commands(self, tmp_path: Path) -> None:
        """Backward compatibility: config without commands section."""
        config_data: dict[str, Any] = {"keys": {}}
        config_file = tmp_path / "config.toml"
        rtoml.dump(config_data, config_file, pretty=True)

        config = Config.from_file(config_file)
        assert config.commands == {}

    def test_to_file_with_commands(self, tmp_path: Path) -> None:
        config = Config(
            commands={"present": {"full_screen": True}},
        )
        config_file = tmp_path / "config.toml"
        config.to_file(config_file)

        # Verify the TOML file contains our commands section
        raw = rtoml.load(config_file)
        assert raw["commands"]["present"]["full_screen"] is True

    def test_merge_commands(self) -> None:
        config_a = Config(
            commands={
                "present": {"full_screen": True},
                "convert": {"one_file": True},
            }
        )
        config_b = Config(
            commands={
                "present": {"hide_mouse": True},
                "render": {"quality": "high"},
            }
        )
        merged = config_a.merge_with(config_b)

        assert merged.commands["present"]["full_screen"] is True
        assert merged.commands["present"]["hide_mouse"] is True
        assert merged.commands["convert"]["one_file"] is True
        assert merged.commands["render"]["quality"] == "high"

    def test_merge_commands_override(self) -> None:
        """Later config overrides earlier values for same key."""
        config_a = Config(commands={"present": {"full_screen": False}})
        config_b = Config(commands={"present": {"full_screen": True}})

        merged = config_a.merge_with(config_b)
        assert merged.commands["present"]["full_screen"] is True


class TestFindConfigFiles:
    """Test config file discovery via directory traversal."""

    def test_no_config_files(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        import manim_slides.defaults as defaults

        monkeypatch.setattr(
            defaults, "GLOBAL_CONFIG_PATH", tmp_path / "xdg" / "config.toml"
        )

        files = find_config_files()
        assert files == []

    def test_finds_local_config(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        import manim_slides.defaults as defaults

        monkeypatch.setattr(
            defaults, "GLOBAL_CONFIG_PATH", tmp_path / "nonexistent" / "config.toml"
        )
        monkeypatch.setattr(defaults, "CONFIG_FILENAME", ".manim-slides.toml")

        config_file = tmp_path / ".manim-slides.toml"
        rtoml.dump({"keys": {}}, config_file, pretty=True)

        files = find_config_files()
        assert config_file.resolve() in [f.resolve() for f in files]

    def test_finds_parent_config(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        subdir = tmp_path / "project" / "subdir"
        subdir.mkdir(parents=True)
        monkeypatch.chdir(subdir)
        import manim_slides.defaults as defaults

        monkeypatch.setattr(
            defaults, "GLOBAL_CONFIG_PATH", tmp_path / "nonexistent" / "config.toml"
        )
        monkeypatch.setattr(defaults, "CONFIG_FILENAME", ".manim-slides.toml")

        parent_config = tmp_path / "project" / ".manim-slides.toml"
        rtoml.dump({"keys": {}}, parent_config, pretty=True)

        files = find_config_files()
        assert parent_config.resolve() in [f.resolve() for f in files]

    def test_priority_order(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """CWD config should come after (= higher priority) parent config."""
        subdir = tmp_path / "project"
        subdir.mkdir()
        monkeypatch.chdir(subdir)
        import manim_slides.defaults as defaults

        monkeypatch.setattr(
            defaults, "GLOBAL_CONFIG_PATH", tmp_path / "nonexistent" / "config.toml"
        )
        monkeypatch.setattr(defaults, "CONFIG_FILENAME", ".manim-slides.toml")

        parent_config = tmp_path / ".manim-slides.toml"
        local_config = subdir / ".manim-slides.toml"
        rtoml.dump({"keys": {}}, parent_config, pretty=True)
        rtoml.dump({"keys": {}}, local_config, pretty=True)

        files = find_config_files()
        resolved = [f.resolve() for f in files]
        parent_idx = resolved.index(parent_config.resolve())
        local_idx = resolved.index(local_config.resolve())
        assert parent_idx < local_idx, (
            "Parent config should come before local (lower priority)"
        )

    def test_finds_global_config(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Global config file is found and has lowest priority."""
        monkeypatch.chdir(tmp_path)
        import manim_slides.defaults as defaults

        global_config = tmp_path / "global_config" / "config.toml"
        global_config.parent.mkdir(parents=True)
        rtoml.dump({"keys": {}}, global_config, pretty=True)
        monkeypatch.setattr(defaults, "GLOBAL_CONFIG_PATH", global_config)
        monkeypatch.setattr(defaults, "CONFIG_FILENAME", ".manim-slides.toml")

        local_config = tmp_path / ".manim-slides.toml"
        rtoml.dump({"keys": {}}, local_config, pretty=True)

        files = find_config_files()
        resolved = [f.resolve() for f in files]
        assert resolved[0] == global_config.resolve(), (
            "Global config should be first (lowest priority)"
        )


class TestLoadMergedConfig:
    """Test merged config loading."""

    def test_explicit_path(self, tmp_path: Path) -> None:
        config_file = tmp_path / "my-config.toml"
        rtoml.dump(
            {"commands": {"present": {"full_screen": True}}},
            config_file,
            pretty=True,
        )
        config = load_merged_config(explicit_path=config_file)
        assert config.commands["present"]["full_screen"] is True

    def test_explicit_path_missing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """If explicit path doesn't exist, fall back to discovery."""
        monkeypatch.chdir(tmp_path)
        import manim_slides.defaults as defaults

        monkeypatch.setattr(
            defaults, "GLOBAL_CONFIG_PATH", tmp_path / "nonexistent" / "config.toml"
        )

        config = load_merged_config(explicit_path=tmp_path / "nonexistent.toml")
        assert config.commands == {}

    def test_merges_parent_and_local(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        subdir = tmp_path / "project"
        subdir.mkdir()
        monkeypatch.chdir(subdir)
        import manim_slides.defaults as defaults

        monkeypatch.setattr(
            defaults, "GLOBAL_CONFIG_PATH", tmp_path / "nonexistent" / "config.toml"
        )
        monkeypatch.setattr(defaults, "CONFIG_FILENAME", ".manim-slides.toml")

        rtoml.dump(
            {"commands": {"present": {"full_screen": True}}},
            tmp_path / ".manim-slides.toml",
            pretty=True,
        )
        rtoml.dump(
            {"commands": {"present": {"hide_mouse": True}}},
            subdir / ".manim-slides.toml",
            pretty=True,
        )

        config = load_merged_config()
        assert config.commands["present"]["full_screen"] is True
        assert config.commands["present"]["hide_mouse"] is True

    def test_local_overrides_parent(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Local config values override parent config values."""
        subdir = tmp_path / "project"
        subdir.mkdir()
        monkeypatch.chdir(subdir)
        import manim_slides.defaults as defaults

        monkeypatch.setattr(
            defaults, "GLOBAL_CONFIG_PATH", tmp_path / "nonexistent" / "config.toml"
        )
        monkeypatch.setattr(defaults, "CONFIG_FILENAME", ".manim-slides.toml")

        rtoml.dump(
            {"commands": {"present": {"full_screen": False}}},
            tmp_path / ".manim-slides.toml",
            pretty=True,
        )
        rtoml.dump(
            {"commands": {"present": {"full_screen": True}}},
            subdir / ".manim-slides.toml",
            pretty=True,
        )

        config = load_merged_config()
        assert config.commands["present"]["full_screen"] is True
