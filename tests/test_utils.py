from pathlib import Path

import av

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


def test_reverse_video_file_segmented(video_file: Path, tmp_path: Path) -> None:
    # Regression test for #562 / #569: the segmented path runs a
    # multiprocessing pool while the parent still holds an open PyAV input
    # container. With the previous fork-based pool this could deadlock
    # (forked children inherit held FFmpeg/tqdm locks); with the spawn-based
    # pool it must complete and produce a decodable, non-empty video.
    dest = tmp_path / "reversed.mp4"

    reverse_video_file(video_file, dest, max_segment_duration=0.5)

    assert dest.exists()
    with av.open(str(dest)) as container:
        frames = sum(1 for _ in container.decode(video=0))
    assert frames > 0
