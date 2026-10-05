import multiprocessing
import os
import shutil
import signal
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

import av
import numpy as np
import pytest
from click.testing import CliRunner

from manim_slides.__main__ import cli
from manim_slides.utils import (
    concatenate_video_files,
    merge_basenames,
    reverse_video_file,
)


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


def assert_has_decodable_video_stream(dest: Path) -> None:
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

    assert_has_decodable_video_stream(dest)


def test_concatenate_video_files_quoted_path(video_file: Path, tmp_path: Path) -> None:
    # A single quote in a path used to terminate the quoted list entry early,
    # making the entry unparsable for the concat demuxer.
    quoted_dir = tmp_path / "John's slides"
    quoted_dir.mkdir()
    src = quoted_dir / video_file.name
    shutil.copy(video_file, src)
    dest = tmp_path / "out.mp4"

    concatenate_video_files([src, src], dest)

    assert_has_decodable_video_stream(dest)


def test_issue540(slides_file: Path) -> None:
    runner = CliRunner()

    with runner.isolated_filesystem():
        results = runner.invoke(cli, ["render", str(slides_file), "Issue540", "-ql"])

        assert results.exit_code == 0, results.output


def test_merge_basenames_short_hash() -> None:
    """Hash is truncated to 16 hex chars to keep paths under Windows MAX_PATH."""
    paths = [Path("a/b/c/very_long_partial_movie_file_name.mp4")]
    merged = merge_basenames(paths)
    # Stem should be at most 16 hex characters (plus extension)
    assert len(merged.stem) == 16
    assert all(c in "0123456789abcdef" for c in merged.stem)


@pytest.fixture
def reversal_video(tmp_path: Path) -> Path:
    src = tmp_path / "src.mp4"

    with av.open(str(src), mode="w") as container:
        stream = container.add_stream("libx264", rate=2)
        stream.width = 16
        stream.height = 16
        stream.pix_fmt = "yuv420p"
        stream.codec_context.gop_size = 1

        for value in range(6):
            array = np.full((16, 16, 3), value * 40, dtype=np.uint8)
            frame = av.VideoFrame.from_ndarray(array, format="rgb24")
            for packet in stream.encode(frame):
                container.mux(packet)

        for packet in stream.encode():
            container.mux(packet)

    return src


def assert_reversed_frames(src: Path, dest: Path) -> None:
    def values(path: Path) -> list[float]:
        with av.open(str(path)) as container:
            return [
                float(frame.to_ndarray(format="gray").mean())
                for frame in container.decode(video=0)
            ]

    expected = values(src)[::-1]
    assert len(expected) == 6
    # Re-encoding is lossy. Check every frame, including count and brightness,
    # so an empty, constant, or incomplete output cannot satisfy the test.
    np.testing.assert_allclose(values(dest), expected, atol=3)


@pytest.mark.parametrize("num_processes", [1, 2])
def test_reverse_video_file_with_unordered_segments(
    reversal_video: Path, monkeypatch: pytest.MonkeyPatch, num_processes: int
) -> None:
    dest = reversal_video.with_name("dest.mp4")

    original_iterdir = Path.iterdir

    def reversed_iterdir(path: Path) -> Iterator[Path]:
        return iter(reversed(list(original_iterdir(path))))

    with monkeypatch.context() as patch:
        patch.setattr(Path, "iterdir", reversed_iterdir)
        reverse_video_file(
            reversal_video,
            dest,
            max_segment_duration=1.0,
            num_processes=num_processes,
            disable=True,
        )

    assert_reversed_frames(reversal_video, dest)


@pytest.mark.skipif(
    "fork" not in multiprocessing.get_all_start_methods(), reason="requires fork"
)
@pytest.mark.parametrize("num_processes", [1, 2])
def test_reverse_video_file_with_inherited_renderer_lock(
    reversal_video: Path, data_folder: Path, num_processes: int
) -> None:
    dest = reversal_video.with_name("dest.mp4")
    with subprocess.Popen(
        [
            sys.executable,
            str(data_folder / "reversal_deadlock.py"),
            str(reversal_video),
            str(dest),
            str(num_processes),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        start_new_session=True,
    ) as process:
        try:
            output, _ = process.communicate(timeout=30)
        except subprocess.TimeoutExpired:
            # Kill the whole pool, not just the parent, so a regression cannot
            # leave hung workers behind or prevent the remaining tests running.
            os.killpg(process.pid, signal.SIGKILL)
            output, _ = process.communicate()
            pytest.fail(f"Segmented reversal stalled with an inherited lock:\n{output}")

        assert process.returncode == 0, output

    assert_reversed_frames(reversal_video, dest)
