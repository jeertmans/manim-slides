from pathlib import Path

import click
import pytest
from click.testing import CliRunner

from manim_slides.commons import (
    config_options,
    config_path_option,
    folder_path_option,
    verbosity_option,
)


def test_config_options() -> None:
    @click.command()
    @config_options
    def main(config_path: Path, force: bool, merge: bool) -> None:
        pass

    runner = CliRunner()

    with runner.isolated_filesystem():
        with open("config.json", "w") as f:
            f.write("Hello world!")

        result = runner.invoke(main, ["--config", "config.json", "--force", "--merge"])

        assert result.exit_code == 0

        result = runner.invoke(main, ["-c", "config.json", "-f", "-m"])


def test_config_path_option() -> None:
    @click.command()
    @config_path_option
    def main(config_path: Path) -> None:
        pass

    runner = CliRunner()

    with runner.isolated_filesystem() as temp_dir:
        with open("config.json", "w") as f:
            f.write("Hello world!")

        result = runner.invoke(main, ["--config", "config.json"])

        assert result.exit_code == 0

        result = runner.invoke(main, ["-c", "config.json"])

        assert result.exit_code == 0

        result = runner.invoke(main, ["--config", "unexisting.json"])

        assert result.exit_code == 0

        result = runner.invoke(main, ["--config", "unexisting"])

        assert result.exit_code == 0

        result = runner.invoke(main, ["--config", temp_dir])

        assert result.exit_code != 0


def test_folder_path_option() -> None:
    @click.command()
    @folder_path_option
    def main(folder: Path) -> None:
        pass

    runner = CliRunner()

    with runner.isolated_filesystem() as temp_dir:
        with open("file.txt", "w") as f:
            f.write("Hello world!")

        result = runner.invoke(main, ["--folder", "file.txt"])

        assert result.exit_code != 0

        result = runner.invoke(main, ["--folder", "unexisting.txt"])

        assert result.exit_code != 0

        result = runner.invoke(main, ["--folder", "unexisting"])

        assert result.exit_code != 0

        result = runner.invoke(main, ["--folder", temp_dir])

        assert result.exit_code == 0


@pytest.mark.parametrize(
    ("verbosity",),
    [("DEBUG",), ("info",), ("waRNING",), ("eRRor",), ("CrItIcAl",)],
)
def test_valid_verbosity_option(verbosity: str) -> None:
    @click.command()
    @verbosity_option
    def main() -> None:
        pass

    runner = CliRunner()
    result = runner.invoke(main, ["-v", verbosity])

    assert result.exit_code == 0

    result = runner.invoke(main, ["--verbosity", verbosity])

    assert result.exit_code == 0

    with runner.isolation(env={"MANIM_SLIDES_VERBOSITY": verbosity}):
        result = runner.invoke(main)

        assert result.exit_code == 0


@pytest.mark.parametrize(
    ("verbosity",), [("test",), ("deebug",), ("warn",), ("errors",)]
)
def test_invalid_verbosity_option(verbosity: str) -> None:
    @click.command()
    @verbosity_option
    def main() -> None:
        pass

    runner = CliRunner()
    result = runner.invoke(main, ["-v", verbosity])

    assert result.exit_code != 0

    result = runner.invoke(main, ["--verbosity", verbosity])

    assert result.exit_code != 0

    with runner.isolation(env={"MANIM_SLIDES_VERBOSITY": verbosity}):
        result = runner.invoke(main)

        assert result.exit_code != 0
