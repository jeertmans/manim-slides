from pathlib import Path

from click.testing import CliRunner

from manim_slides.__main__ import cli


def test_help() -> None:
    runner = CliRunner()
    results = runner.invoke(cli, ["-S", "--help"])

    assert results.exit_code == 0

    results = runner.invoke(cli, ["-S", "-h"])

    assert results.exit_code == 0


def test_defaults_to_present(folder_path: Path) -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        print(folder_path)
        results = runner.invoke(
            cli, ["BasicExample", "--folder", str(folder_path), "-s"]
        )

        assert results.exit_code == 0


def test_present(folder_path: Path) -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        results = runner.invoke(
            cli, ["present", "BasicExample", "--folder", str(folder_path), "-s"]
        )

        assert results.exit_code == 0


def test_convert(folder_path: Path) -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        results = runner.invoke(
            cli,
            [
                "convert",
                "BasicExample",
                "basic_example.html",
                "--folder",
                str(folder_path),
            ],
        )

        assert results.exit_code == 0


def test_init() -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        results = runner.invoke(
            cli,
            [
                "init",
                "--force",
            ],
        )

        assert results.exit_code == 0


def test_list_scenes(folder_path: Path) -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        results = runner.invoke(
            cli,
            [
                "list-scenes",
                "--folder",
                str(folder_path),
            ],
        )

        assert results.exit_code == 0
        assert "BasicExample" in results.output


def test_wizard() -> None:
    # TODO
    pass
