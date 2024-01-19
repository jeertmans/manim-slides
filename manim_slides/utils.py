import hashlib
import tempfile
from pathlib import Path
from typing import List

import av

from .logger import logger


def concatenate_video_files(files: List[Path], dest: Path) -> None:
    """Concatenate multiple video files into one."""
    f = tempfile.NamedTemporaryFile(mode="w", delete=False)
    f.writelines(f"file '{path.absolute()}'\n" for path in files)
    f.close()

    input_ = av.open(f.name, options={"safe": "0"}, format="concat")
    input_stream = input_.streams.video[0]
    output = av.open(str(dest), mode="w")
    output_stream = output.add_stream(
        template=input_stream,
    )

    for packet in input_.demux(input_stream):
        # We need to skip the "flushing" packets that `demux` generates.
        if packet.dts is None:
            continue

        # We need to assign the packet to the new stream.
        packet.stream = output_stream
        output.mux(packet)

    input_.close()
    output.close()


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


def link_nodes(*nodes: av.filter.context.FilterContext) -> None:
    """Code from https://github.com/PyAV-Org/PyAV/issues/239."""
    for c, n in zip(nodes, nodes[1:]):
        c.link_to(n)


def reverse_video_file(src: Path, dest: Path) -> None:
    """Reverses a video file, writting the result to `dest`."""
    input_ = av.open(str(src))
    input_stream = input_.streams.video[0]
    output = av.open(str(dest), mode="w")
    output_stream = output.add_stream(codec_name="libx264", rate=input_stream.base_rate)
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
    for frame in input_.decode(video=0):
        graph.push(frame)
        frames_count += 1

    graph.push(None)  # EOF: https://github.com/PyAV-Org/PyAV/issues/886.

    for _ in range(frames_count):
        frame = graph.pull()
        frame.pict_type = 5  # Otherwise we get a warning saying it is changed
        output.mux(output_stream.encode(frame))

    for packet in output_stream.encode():
        output.mux(packet)

    input_.close()
    output.close()
