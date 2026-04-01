import hashlib
import os
import shutil
import subprocess
import tempfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any, Optional

import av

from .logger import logger

AV_VERSION_14 = int(av.__version__.split(".", maxsplit=1)[0]) >= 14


def concatenate_video_files(files: list[Path], dest: Path) -> None:
    """Concatenate multiple video files into one using ffmpeg."""
    if len(files) == 1:
        shutil.copy(files[0], dest)
        return

    def _filter(files: list[Path]) -> Iterator[Path]:
        """Patch possibly empty video files."""
        for file in files:
            with av.open(str(file)) as container:
                if len(container.streams.video) > 0:
                    yield file
                else:
                    logger.warning(
                        f"Skipping video file {file} because it does "
                        "not contain any video stream. "
                        "This is probably caused by Manim, see: "
                        "https://github.com/jeertmans/manim-slides/issues/390."
                    )

    filtered_files = list(_filter(files))
    if len(filtered_files) == 0:
        raise ValueError("No valid video files to concatenate!")
    elif len(filtered_files) == 1:
        shutil.copy(filtered_files[0], dest)
        return

    # Use ffmpeg concat demuxer - more robust than PyAV
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as f:
        for file in filtered_files:
            # Escape single quotes in filename for ffmpeg
            escaped = str(file).replace("'", "'\\''")
            f.write(f"file '{escaped}'\n")
        concat_file = f.name

    try:
        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            concat_file,
            "-c",
            "copy",  # Stream copy (no re-encoding)
            "-movflags",
            "+faststart",
            str(dest),
        ]

        logger.debug(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        if result.returncode == 0:
            logger.info(
                f"Successfully concatenated {len(filtered_files)} files to {dest}"
            )
        else:
            raise RuntimeError(f"ffmpeg failed: {result.stderr}")

    except subprocess.CalledProcessError as e:
        logger.error(f"ffmpeg concat failed: {e.stderr}")
        # Fallback: try with re-encoding
        logger.info("Attempting fallback with re-encoding...")
        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            concat_file,
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            "-movflags",
            "+faststart",
            str(dest),
        ]
        subprocess.run(cmd, capture_output=True, text=True, check=True)

    finally:
        os.unlink(concat_file)


def merge_basenames(files: list[Path]) -> Path:
    """Merge multiple filenames by concatenating basenames."""
    if len(files) == 0:
        raise ValueError("Cannot merge an empty list of files!")

    dirname: Path = files[0].parent
    ext = files[0].suffix

    basenames = list(file.stem for file in files)

    basenames_str = ",".join(f"{len(b)}:{b}" for b in basenames)

    # We use hashes to prevent too-long filenames, see issue #123:
    # https://github.com/jeertmans/manim-slides/issues/123
    basename = hashlib.sha256(basenames_str.encode()).hexdigest()

    logger.debug(f"Generated a new basename for basenames: {basenames} -> '{basename}'")

    return dirname.joinpath(basename + ext)


def link_nodes(*nodes: av.filter.context.FilterContext) -> None:
    """Code from https://github.com/PyAV-Org/PyAV/issues/239."""
    for c, n in zip(nodes, nodes[1:]):
        c.link_to(n)


def reverse_video_file_in_one_chunk(src_and_dest: tuple[Path, Path]) -> None:
    """Reverses a video file, writing the result to `dest`."""
    src, dest = src_and_dest
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(src),
        "-vf",
        "reverse",
        "-af",
        "areverse",
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        str(dest),
    ]
    subprocess.run(cmd, capture_output=True, check=True)


def reverse_video_file(
    src: Path,
    dest: Path,
    max_segment_duration: Optional[float] = 4.0,
    num_processes: Optional[int] = None,
    **tqdm_kwargs: Any,
) -> None:
    """Reverses a video file, writing the result to `dest`."""
    # Use ffmpeg for reversing - simpler and more reliable
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(src),
        "-vf",
        "reverse",
        "-af",
        "areverse",
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        str(dest),
    ]
    subprocess.run(cmd, capture_output=True, check=True)
