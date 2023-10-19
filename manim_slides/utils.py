import hashlib
import subprocess
import tempfile
from pathlib import Path
from typing import List

from .logger import logger


def concatenate_video_files(ffmpeg_bin: Path, files: List[Path], dest: Path) -> None:
    """Concatenate multiple video files into one."""
    f = tempfile.NamedTemporaryFile(mode="w", delete=False)
    f.writelines(f"file '{path.absolute()}'\n" for path in files)
    f.close()

    command: List[str] = [
        str(ffmpeg_bin),
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        f.name,
        "-c",
        "copy",
        str(dest),
        "-y",
    ]
    logger.debug(" ".join(command))
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = process.communicate()

    if output:
        logger.debug(output.decode())

    if error:
        logger.debug(error.decode())

    if not dest.exists():
        raise ValueError(
            "could not properly concatenate files, use `-v DEBUG` for more details"
        )


def merge_basenames(files: List[Path]) -> Path:
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


def reverse_video_file(ffmpeg_bin: Path, src: Path, dst: Path) -> None:
    """Reverses a video file, writting the result to `dst`."""
    command = [str(ffmpeg_bin), "-y", "-i", str(src), "-vf", "reverse", str(dst)]
    logger.debug(" ".join(command))
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = process.communicate()

    if output:
        logger.debug(output.decode())

    if error:
        logger.debug(error.decode())
