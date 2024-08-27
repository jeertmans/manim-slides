import hashlib
import os
import tempfile
from collections.abc import Iterator
from pathlib import Path

import av

from .logger import logger


def concatenate_video_files(files: list[Path], dest: Path) -> None:
    """Concatenate multiple video files into one."""

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


def reverse_video_file(src: Path, dest: Path) -> None:
    """Reverses a video file, writing the result to `dest`."""
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
            frame.pict_type = 5  # Otherwise we get a warning saying it is changed
            output_container.mux(output_stream.encode(frame))

        for packet in output_stream.encode():
            output_container.mux(packet)
