from collections.abc import Iterator
from pathlib import Path

import av
import numpy as np
import pytest

from manim_slides.utils import merge_basenames, reverse_video_file


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


def test_reverse_video_file_with_unordered_segments(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    src = tmp_path / "src.mp4"
    dest = tmp_path / "dest.mp4"

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

    original_iterdir = Path.iterdir

    def reversed_iterdir(path: Path) -> Iterator[Path]:
        return iter(reversed(list(original_iterdir(path))))

    monkeypatch.setattr(Path, "iterdir", reversed_iterdir)

    reverse_video_file(
        src,
        dest,
        max_segment_duration=1.0,
        num_processes=1,
        disable=True,
    )

    with av.open(str(dest)) as container:
        values = [
            float(frame.to_ndarray(format="gray").mean())
            for frame in container.decode(video=0)
        ]

    assert values == sorted(values, reverse=True)
