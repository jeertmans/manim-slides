from pathlib import Path

import pytest
from click.testing import CliRunner

from manim_slides.config import Config
from manim_slides.config_lookup import (
    list_config_files,
    list_local_config_files,
    load_merged_config,
    validate_defaults_against_command,
)


class TestListLocalConfigFiles:
    def test_no_config_file(self, tmp_path: Path) -> None:
        assert list_local_config_files(folder=tmp_path) == []

    def test_reads_config_in_folder(self, tmp_path: Path) -> None:
        config_file = tmp_path / ".manim-slides.toml"
        config_file.touch()

        assert list_local_config_files(folder=tmp_path) == [config_file]

    def test_stops_at_parent_config(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        parent_config = tmp_path / ".manim-slides.toml"
        parent_config.touch()

        subfolder = tmp_path / "a" / "b"
        subfolder.mkdir(parents=True)

        assert list_local_config_files(folder=subfolder) == [parent_config]

    def test_closest_config_has_precedence(self, tmp_path: Path) -> None:
        parent_config = tmp_path / ".manim-slides.toml"
        parent_config.touch()

        subfolder = tmp_path / "a"
        subfolder.mkdir()
        child_config = subfolder / ".manim-slides.toml"
        child_config.touch()

        assert list_local_config_files(folder=subfolder) == [
            parent_config,
            child_config,
        ]

    def test_custom_config_path(self, tmp_path: Path) -> None:
        config_file = tmp_path / "custom.toml"
        config_file.touch()

        assert list_local_config_files(folder=tmp_path, config_path=config_file) == [
            config_file
        ]

    def test_relative_config_path(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)

        config_file = tmp_path / "custom.toml"
        config_file.touch()

        # A relative config path is interpreted as relative to FOLDER.
        assert list_local_config_files(
            folder=tmp_path, config_path=Path("custom.toml")
        ) == [config_file]


class TestListConfigFiles:
    def test_includes_global_config_first(
        self, tmp_path: Path, global_config_path: Path
    ) -> None:
        global_config_path.parent.mkdir(parents=True, exist_ok=True)
        global_config_path.touch()

        local_file = tmp_path / ".manim-slides.toml"
        local_file.touch()

        files = list_config_files(folder=tmp_path)

        assert files[0] == global_config_path
        assert local_file in files

    def test_global_config_only(self, tmp_path: Path, global_config_path: Path) -> None:
        global_config_path.parent.mkdir(parents=True, exist_ok=True)
        global_config_path.touch()

        # Use a folder without any local config file, so the test does
        # not depend on the contents of the current working directory.
        assert list_config_files(folder=tmp_path) == [global_config_path]

    def test_no_config_files(self, tmp_path: Path, global_config_path: Path) -> None:
        assert list_config_files(folder=tmp_path) == []

    def test_explicit_config_path_outside_tree(self, tmp_path: Path) -> None:
        outside = tmp_path / "elsewhere" / "custom.toml"
        outside.parent.mkdir()
        outside.touch()

        work = tmp_path / "work"
        work.mkdir()

        assert list_config_files(folder=work, config_path=outside) == [outside]

    def test_explicit_config_path_not_duplicated(self, tmp_path: Path) -> None:
        config_file = tmp_path / "custom.toml"
        config_file.touch()

        files = list_config_files(folder=tmp_path, config_path=config_file)

        assert files == [config_file]


class TestLoadMergedConfig:
    def test_global_then_local_precedence(
        self, tmp_path: Path, global_config_path: Path
    ) -> None:
        global_config_path.parent.mkdir(parents=True, exist_ok=True)
        global_config_path.write_text(
            '[defaults.present]\nfull_screen = true\nfolder = "global"\n'
        )

        local_config = tmp_path / ".manim-slides.toml"
        local_config.write_text('[defaults.present]\nfolder = "local"\n')

        config = load_merged_config(folder=tmp_path)

        assert config.defaults.root == {
            "present": {"full_screen": True, "folder": "local"}
        }

    def test_keys_are_also_merged(
        self, tmp_path: Path, global_config_path: Path
    ) -> None:
        global_config_path.parent.mkdir(parents=True, exist_ok=True)
        global_config_path.write_text("[keys]\n[keys.QUIT]\nids = [81]\n")

        local_config = tmp_path / ".manim-slides.toml"
        local_config.write_text("[keys]\n[keys.QUIT]\nids = [81, 100]\n")

        config = load_merged_config(folder=tmp_path)

        assert 100 in config.keys.QUIT.ids

    def test_invalid_file_is_skipped_with_warning(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        (tmp_path / ".manim-slides.toml").write_text("not a valid toml file [")

        with caplog.at_level("WARNING", logger="manim-slides"):
            config = load_merged_config(folder=tmp_path)

        assert config == Config()
        assert any(
            "Ignoring invalid configuration file" in record.message
            for record in caplog.records
        )

    def test_scalar_defaults_table_is_skipped_with_warning(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        (tmp_path / ".manim-slides.toml").write_text("defaults = 5\n")

        with caplog.at_level("WARNING", logger="manim-slides"):
            config = load_merged_config(folder=tmp_path)

        assert config == Config()
        assert any(
            "Ignoring invalid configuration file" in record.message
            for record in caplog.records
        )

    def test_deep_folder_tree_precedence(self, tmp_path: Path) -> None:
        (tmp_path / ".manim-slides.toml").write_text(
            '[defaults.present]\nfolder = "grandparent"\n'
        )
        child = tmp_path / "a"
        child.mkdir()
        (child / ".manim-slides.toml").write_text(
            '[defaults.present]\nfolder = "parent"\n'
        )
        grandchild = child / "b"
        grandchild.mkdir()
        (grandchild / ".manim-slides.toml").write_text(
            "[defaults.present]\nskip_all = true\n"
        )

        config = load_merged_config(folder=grandchild)

        assert config.defaults.root == {
            "present": {"folder": "parent", "skip_all": True}
        }

    def test_no_files(self, tmp_path: Path) -> None:
        assert load_merged_config(folder=tmp_path) == Config()


class TestValidateDefaultsAgainstCommand:
    def test_known_and_unknown_options(self) -> None:
        from manim_slides.present import list_scenes

        defaults = {"folder": "slides", "unknown_option": True}

        unknown = validate_defaults_against_command(list_scenes, defaults)

        assert unknown == ["unknown_option"]

    def test_all_known(self) -> None:
        from manim_slides.present import list_scenes

        assert validate_defaults_against_command(list_scenes, {"folder": "x"}) == []


@pytest.fixture
def config_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    path = tmp_path / ".manim-slides.toml"
    path.touch()
    return path


class TestCliDefaultMap:
    def test_defaults_applied(self, config_file: Path, slides_folder: Path) -> None:
        from manim_slides.__main__ import cli

        config_file.write_text(
            f'[defaults.list-scenes]\nfolder = "{slides_folder.as_posix()}"\n'
        )

        runner = CliRunner()
        result = runner.invoke(cli, ["list-scenes"])

        assert result.exit_code == 0
        assert "BasicSlide" in result.output

    def test_command_line_overrides_config(
        self, config_file: Path, slides_folder: Path
    ) -> None:
        from manim_slides.__main__ import cli

        config_file.write_text('[defaults.list-scenes]\nfolder = "nowhere"\n')

        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["list-scenes", "--folder", str(slides_folder)],
        )

        assert result.exit_code == 0
        assert "BasicSlide" in result.output

    def test_unknown_option_warns(
        self,
        config_file: Path,
        slides_folder: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        from manim_slides.__main__ import cli

        config_file.write_text(
            f"[defaults.list-scenes]\n"
            f'folder = "{slides_folder.as_posix()}"\n'
            f"unknown_option = true\n"
        )

        with caplog.at_level("WARNING", logger="manim-slides"):
            runner = CliRunner()
            result = runner.invoke(cli, ["list-scenes"])

        assert result.exit_code == 0
        assert "BasicSlide" in result.output
        assert any(
            "Ignoring unknown configuration options: list-scenes.unknown_option"
            in record.message
            for record in caplog.records
        )
