import shutil
from pathlib import Path

import av
import pytest

from manim_slides.utils import concatenate_video_files, merge_basenames


def test_merge_basenames(paths: list[Path]) -> None:
    path = merge_basenames(paths)
    assert path.suffix == paths[0].suffix
    assert path.parent == paths[0].parent


def test_merge_basenames_same_with_different_parent_directories(
    paths: list[Path],
) -> None:
    d1 = Path("a/b/c")
    d2 = Path("d/e/f")
    p1 = d1 / "one.txt"
    p2 = d1 / "a/b/c/two.txt"
    p3 = d2 / "d/e/f/one.txt"
    p4 = d2 / "d/e/f/two.txt"

    assert merge_basenames([p1, p2]).name == merge_basenames([p3, p4]).name


def _assert_decodable(dest: Path) -> None:
    assert dest.exists()
    with av.open(str(dest)) as container:
        assert sum(1 for _ in container.decode(video=0)) > 0


def test_concatenate_video_files_relative_paths(
    video_file: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The concat list file lives in the system temp folder, and the concat
    # demuxer resolves relative entries against *that* folder — so relative
    # input paths used to fail with FileNotFoundError.
    monkeypatch.chdir(video_file.parent)
    relative = Path(video_file.name)
    dest = tmp_path / "out.mp4"

    concatenate_video_files([relative, relative], dest)

    _assert_decodable(dest)


def test_concatenate_video_files_quoted_path(video_file: Path, tmp_path: Path) -> None:
    # A single quote in a path used to terminate the quoted list entry early,
    # making the entry unparsable for the concat demuxer.
    quoted_dir = tmp_path / "John's slides"
    quoted_dir.mkdir()
    src = quoted_dir / video_file.name
    shutil.copy(video_file, src)
    dest = tmp_path / "out.mp4"

    concatenate_video_files([src, src], dest)

    _assert_decodable(dest)
