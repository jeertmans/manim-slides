import hashlib
import os
import shutil
import subprocess  # nosec B404
import tempfile
from collections.abc import Iterator
from multiprocessing import Pool
from pathlib import Path
from typing import Any, Optional

import av
from tqdm import tqdm

from .logger import logger


def get_duration_ms(file: Path) -> float:
    """Return video duration in milliseconds."""
    with av.open(str(file)) as container:
        video = container.streams.video[0]
        return float(1000 * video.duration * video.time_base)


def get_duration_seconds(file: Path) -> float:
    """Return video duration in seconds."""
    return get_duration_ms(file) / 1000.0


def extract_video_segment(
    src: Path, dest: Path, start: float, end: float, *, accurate: bool = False
) -> None:
    """
    Extract a [start, end] video segment (in seconds) into dest using ffmpeg.

    This function uses subprocess to call ffmpeg directly. While subprocess usage
    can be a security concern, this implementation is safe because:
    1. All inputs are validated before use
    2. Arguments are passed as a list (not shell string)
    3. shell=False prevents shell injection
    4. ffmpeg path is resolved via shutil.which()

    :param accurate: If True, re-encodes for frame-accurate cuts. If False, uses
        codec copy which is faster but cuts only at keyframes.
    """
    if not src.exists():
        raise FileNotFoundError(f"Source video file does not exist: {src}")
    if not src.is_file():
        raise ValueError(f"Source path is not a file: {src}")

    dest.parent.mkdir(parents=True, exist_ok=True)

    # Add small epsilon to include the frame at end_time
    # ffmpeg's -t duration excludes frames at exactly start+duration
    epsilon = 0.001
    duration = max(end - start + epsilon, 0.0)
    if duration <= epsilon:
        shutil.copy(src, dest)
        return

    if start < 0.0 or end < 0.0:
        raise ValueError(f"Time values must be non-negative: start={start}, end={end}")

    # Verify ffmpeg is available
    ffmpeg_path = shutil.which("ffmpeg")
    if not ffmpeg_path:
        raise RuntimeError("ffmpeg not found in PATH")

    # Build command with validated, safe arguments
    if accurate:
        # Re-encode for frame-accurate cuts
        command = [
            ffmpeg_path,
            "-y",  # Overwrite output file
            "-ss",
            f"{start:.3f}",  # Start time (validated float)
            "-i",
            str(src.resolve()),  # Input file (validated Path)
            "-t",
            f"{duration:.3f}",  # Duration (validated float)
            "-c:v",
            "libx264",  # Re-encode video
            "-c:a",
            "aac",  # Re-encode audio
            str(dest.resolve()),  # Output file (validated Path)
        ]
    else:
        # Fast copy without re-encoding (keyframe cuts only)
        command = [
            ffmpeg_path,
            "-y",  # Overwrite output file
            "-ss",
            f"{start:.3f}",  # Start time (validated float)
            "-i",
            str(src.resolve()),  # Input file (validated Path)
            "-t",
            f"{duration:.3f}",  # Duration (validated float)
            "-c",
            "copy",  # Copy codec (no re-encoding)
            str(dest.resolve()),  # Output file (validated Path)
        ]

    # Execute with shell=False to prevent injection
    process = subprocess.run(  # nosec B603
        command,
        capture_output=True,
        check=False,
        shell=False,
    )

    if process.returncode != 0:
        raise RuntimeError(
            f"ffmpeg failed to extract video segment:\n{process.stderr.decode().strip()}"
        )


def concatenate_video_files(files: list[Path], dest: Path) -> None:
    """Concatenate multiple video files into one."""
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

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.writelines(f"file '{file}'\n" for file in _filter(files))
        tmp_file = f.name

    with (
        av.open(tmp_file, format="concat", options={"safe": "0"}) as input_container,
        av.open(str(dest), mode="w") as output_container,
    ):
        input_video_stream = input_container.streams.video[0]
        output_video_stream = output_container.add_stream(
            template=input_video_stream,
        )

        if len(input_container.streams.audio) > 0:
            input_audio_stream = input_container.streams.audio[0]
            output_audio_stream = output_container.add_stream(
                template=input_audio_stream,
            )

        for packet in input_container.demux():
            if packet.dts is None:
                continue

            ptype = packet.stream.type

            if ptype == "video":
                packet.stream = output_video_stream
            elif ptype == "audio":
                packet.stream = output_audio_stream
            else:
                continue  # We don't support subtitles
            output_container.mux(packet)

    os.unlink(tmp_file)  # https://stackoverflow.com/a/54768241


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
    with (
        av.open(str(src)) as input_container,
        av.open(str(dest), mode="w") as output_container,
    ):
        input_stream = input_container.streams.video[0]
        output_stream = output_container.add_stream(
            codec_name="libx264", rate=input_stream.base_rate
        )
        output_stream.width = input_stream.width
        output_stream.height = input_stream.height
        output_stream.pix_fmt = input_stream.pix_fmt

        graph = av.filter.Graph()
        link_nodes(
            graph.add_buffer(template=input_stream),
            graph.add("reverse"),
            graph.add("buffersink"),
        )
        graph.configure()

        frames_count = 0
        for frame in input_container.decode(video=0):
            graph.push(frame)
            frames_count += 1

        graph.push(None)  # EOF: https://github.com/PyAV-Org/PyAV/issues/886.

        for _ in range(frames_count):
            frame = graph.pull()
            frame.pict_type = "NONE"  # Otherwise we get a warning saying it is changed
            output_container.mux(output_stream.encode(frame))

        for packet in output_stream.encode():
            output_container.mux(packet)


def reverse_video_file(
    src: Path,
    dest: Path,
    max_segment_duration: Optional[float] = 4.0,
    num_processes: Optional[int] = None,
    **tqdm_kwargs: Any,
) -> None:
    """Reverses a video file, writing the result to `dest`."""
    with av.open(str(src)) as input_container:  # Fast path if file is short enough
        input_stream = input_container.streams.video[0]
        if max_segment_duration is None:
            return reverse_video_file_in_one_chunk((src, dest))
        elif input_stream.duration:
            if (
                float(input_stream.duration * input_stream.time_base)
                <= max_segment_duration
            ):
                return reverse_video_file_in_one_chunk((src, dest))
        else:  # pragma: no cover
            logger.debug(
                f"Could not determine duration of {src}, falling back to segmentation."
            )

        with tempfile.TemporaryDirectory() as tmpdirname:
            tmpdir = Path(tmpdirname)
            with av.open(
                str(tmpdir / f"%04d.{src.suffix}"),
                "w",
                format="segment",
                options={"segment_time": str(max_segment_duration)},
            ) as output_container:
                output_stream = output_container.add_stream(
                    template=input_stream,
                )

                for packet in input_container.demux(input_stream):
                    if packet.dts is None:
                        continue

                    packet.stream = output_stream
                    output_container.mux(packet)

            src_files = list(tmpdir.iterdir())
            rev_files = [
                src_file.with_stem("rev_" + src_file.stem) for src_file in src_files
            ]

            with Pool(num_processes, maxtasksperchild=1) as pool:
                for _ in tqdm(
                    pool.imap_unordered(
                        reverse_video_file_in_one_chunk, zip(src_files, rev_files)
                    ),
                    desc="Reversing large file by cutting it in segments",
                    total=len(src_files),
                    unit=" files",
                    **tqdm_kwargs,
                ):
                    pass  # We just consume the iterator

            concatenate_video_files(rev_files[::-1], dest)
