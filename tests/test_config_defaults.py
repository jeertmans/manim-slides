"""Tests for config file discovery and command defaults."""

from __future__ import annotations

import importlib
import sys
from collections.abc import Iterator
from pathlib import Path
from unittest import mock

import pytest
import rtoml


@pytest.fixture(autouse=True, scope="module")
def patch_qtpy() -> Iterator[None]:
    """Mock qtpy module for the duration of this test module.

    The Config/Keys classes depend on Qt key constants at import time.
    We mock qtpy, then reload manim_slides.config so it picks up the mock.
    After tests, we restore the original state.
    """
    old_qtpy = sys.modules.get("qtpy")
    old_qtpy_core = sys.modules.get("qtpy.QtCore")

    qt_mock = mock.MagicMock()
    qt_mock.QtCore.Qt.Key_Right = 0x01000014
    qt_mock.QtCore.Qt.Key_Left = 0x01000012
    qt_mock.QtCore.Qt.Key_Up = 0x01000013
    qt_mock.QtCore.Qt.Key_Down = 0x01000015
    qt_mock.QtCore.Qt.Key_Space = 0x20
    qt_mock.QtCore.Qt.Key_Q = 0x51
    qt_mock.QtCore.Qt.Key_V = 0x56
    qt_mock.QtCore.Qt.Key_R = 0x52
    qt_mock.QtCore.Qt.Key_F = 0x46
    qt_mock.QtCore.Qt.Key_H = 0x48
    qt_mock.QtCore.Qt.Key_Return = 0x01000004
    qt_mock.QtCore.Qt.Key_Backspace = 0x01000003
    qt_mock.QtCore.Qt.Key_F5 = 0x01000034

    sys.modules["qtpy"] = qt_mock
    sys.modules["qtpy.QtCore"] = qt_mock.QtCore

    import manim_slides.config

    importlib.reload(manim_slides.config)

    yield

    # Restore original modules
    if old_qtpy is None:
        sys.modules.pop("qtpy", None)
    else:
        sys.modules["qtpy"] = old_qtpy

    if old_qtpy_core is None:
        sys.modules.pop("qtpy.QtCore", None)
    else:
        sys.modules["qtpy.QtCore"] = old_qtpy_core

    importlib.reload(manim_slides.config)


class TestConfigWithCommands:
    """Test Config model with command defaults."""

    def test_empty_commands(self) -> None:
        from manim_slides.config import Config

        config = Config()
        assert config.commands == {}
        assert config.get_default_map() == {}

    def test_commands_from_dict(self) -> None:
        from manim_slides.config import Config

        config = Config(
            commands={
                "present": {"full_screen": True, "hide_mouse": True},
                "convert": {"one_file": True},
            }
        )
        assert config.commands["present"]["full_screen"] is True
        assert config.commands["convert"]["one_file"] is True

    def test_get_default_map(self) -> None:
        from manim_slides.config import Config

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
        from manim_slides.config import Config

        config_data: dict[str, object] = {
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
        from manim_slides.config import Config

        config_data: dict[str, object] = {"keys": {}}
        config_file = tmp_path / "config.toml"
        rtoml.dump(config_data, config_file, pretty=True)

        config = Config.from_file(config_file)
        assert config.commands == {}

    def test_to_file_with_commands(self, tmp_path: Path) -> None:
        from manim_slides.config import Config

        config = Config(
            commands={"present": {"full_screen": True}},
        )
        config_file = tmp_path / "config.toml"
        config.to_file(config_file)

        raw = rtoml.load(config_file)
        assert raw["commands"]["present"]["full_screen"] is True

    def test_merge_commands(self) -> None:
        from manim_slides.config import Config

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
        from manim_slides.config import Config

        config_a = Config(commands={"present": {"full_screen": False}})
        config_b = Config(commands={"present": {"full_screen": True}})

        merged = config_a.merge_with(config_b)
        assert merged.commands["present"]["full_screen"] is True


class TestFindConfigFiles:
    """Test config file discovery via directory traversal."""

    def test_no_config_files(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from manim_slides.config import find_config_files

        monkeypatch.chdir(tmp_path)
        files = find_config_files()
        assert files == []

    def test_finds_local_config(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from manim_slides.config import find_config_files

        monkeypatch.chdir(tmp_path)
        config_file = tmp_path / ".manim-slides.toml"
        rtoml.dump({"keys": {}}, config_file, pretty=True)

        files = find_config_files()
        assert config_file.resolve() in [f.resolve() for f in files]

    def test_finds_parent_config(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from manim_slides.config import find_config_files

        subdir = tmp_path / "project" / "subdir"
        subdir.mkdir(parents=True)
        monkeypatch.chdir(subdir)

        parent_config = tmp_path / "project" / ".manim-slides.toml"
        rtoml.dump({"keys": {}}, parent_config, pretty=True)

        files = find_config_files()
        assert parent_config.resolve() in [f.resolve() for f in files]

    def test_priority_order(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """CWD config should come after (= higher priority) parent config."""
        from manim_slides.config import find_config_files

        subdir = tmp_path / "project"
        subdir.mkdir()
        monkeypatch.chdir(subdir)

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


class TestLoadMergedConfig:
    """Test merged config loading."""

    def test_explicit_path(self, tmp_path: Path) -> None:
        from manim_slides.config import load_merged_config

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
        from manim_slides.config import load_merged_config

        monkeypatch.chdir(tmp_path)
        config = load_merged_config(explicit_path=tmp_path / "nonexistent.toml")
        assert config.commands == {}

    def test_merges_parent_and_local(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from manim_slides.config import load_merged_config

        subdir = tmp_path / "project"
        subdir.mkdir()
        monkeypatch.chdir(subdir)

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
        from manim_slides.config import load_merged_config

        subdir = tmp_path / "project"
        subdir.mkdir()
        monkeypatch.chdir(subdir)

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
