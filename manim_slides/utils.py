import hashlib
import os
import shutil
import tempfile
from collections.abc import Iterator
from fractions import Fraction
from multiprocessing import Pool
from pathlib import Path
from typing import Any, Optional, Union, cast

import av
from tqdm import tqdm

from .logger import logger


def _try_add_stream_from_template(
    container: av.container.OutputContainer, template_stream: av.stream.Stream
) -> Optional[av.stream.Stream]:
    try:
        return cast(
            Optional[av.stream.Stream],
            cast(Any, container).add_stream_from_template(template_stream),
        )
    except AttributeError:
        # Older PyAV versions don't expose add_stream_from_template.
        try:
            return cast(
                Optional[av.stream.Stream],
                cast(Any, container).add_stream(template=template_stream),
            )
        except TypeError as exc:
            logger.debug(
                "add_stream(template=...) failed; falling back to manual config.",
                exc_info=exc,
            )
    except (TypeError, ValueError, av.error.FFmpegError) as exc:
        logger.debug(
            "add_stream_from_template failed; falling back to manual config.",
            exc_info=exc,
        )
    return None


def _get_codec_name(template_stream: av.stream.Stream) -> str:
    codec_context = getattr(template_stream, "codec_context", None)
    codec_name = getattr(codec_context, "name", None) if codec_context else None
    if not codec_name:
        codec = getattr(template_stream, "codec", None)
        codec_name = getattr(codec, "name", None) if codec else None
    if codec_name:
        return cast(str, codec_name)
    return "libx264" if template_stream.type == "video" else "aac"


def _get_stream_rate(
    template_stream: av.stream.Stream,
) -> Optional[Union[Fraction, int]]:
    if template_stream.type == "video":
        return cast(
            Optional[Union[Fraction, int]],
            getattr(template_stream, "average_rate", None)
            or getattr(template_stream, "base_rate", None)
            or getattr(template_stream, "rate", None),
        )
    if template_stream.type == "audio":
        return cast(
            Optional[Union[Fraction, int]],
            getattr(template_stream, "rate", None)
            or getattr(template_stream, "sample_rate", None)
            or getattr(template_stream, "average_rate", None),
        )
    return None


def _safe_set_attr(output_stream: av.stream.Stream, attr: str, value: object) -> None:
    if value is None:
        return
    try:
        setattr(output_stream, attr, value)
    except (AttributeError, TypeError, ValueError):
        return


def _copy_video_attrs(
    output_stream: av.stream.Stream, template_stream: av.stream.Stream
) -> None:
    for attr in ("width", "height", "pix_fmt", "time_base", "sample_aspect_ratio"):
        _safe_set_attr(output_stream, attr, getattr(template_stream, attr, None))


def _copy_audio_attrs(
    output_stream: av.stream.Stream, template_stream: av.stream.Stream
) -> None:
    for attr in ("layout", "channels", "format"):
        _safe_set_attr(output_stream, attr, getattr(template_stream, attr, None))
    _safe_set_attr(output_stream, "rate", getattr(template_stream, "rate", None))
    _safe_set_attr(output_stream, "rate", getattr(template_stream, "sample_rate", None))


def _add_stream_from_template(
    container: av.container.OutputContainer, template_stream: av.stream.Stream
) -> av.stream.Stream:
    """Add an output stream that matches the template stream."""
    output_stream = _try_add_stream_from_template(container, template_stream)
    if output_stream is not None:
        return output_stream

    codec_name = _get_codec_name(template_stream)
    rate = _get_stream_rate(template_stream)
    if rate is None:
        output_stream = container.add_stream(codec_name)
    else:
        output_stream = container.add_stream(codec_name, rate=rate)

    if template_stream.type == "video":
        _copy_video_attrs(output_stream, template_stream)
    elif template_stream.type == "audio":
        _copy_audio_attrs(output_stream, template_stream)

    return output_stream


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

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as f:
        f.writelines(f"file '{file}'\n" for file in _filter(files))
        tmp_file = f.name

    with (
        av.open(tmp_file, format="concat", options={"safe": "0"}) as input_container,
        av.open(str(dest), mode="w") as output_container,
    ):
        input_video_stream = input_container.streams.video[0]
        output_video_stream = _add_stream_from_template(
            output_container, input_video_stream
        )

        if len(input_container.streams.audio) > 0:
            input_audio_stream = input_container.streams.audio[0]
            output_audio_stream = _add_stream_from_template(
                output_container, input_audio_stream
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
        cast(Any, output_stream).width = cast(Any, input_stream).width
        cast(Any, output_stream).height = cast(Any, input_stream).height
        cast(Any, output_stream).pix_fmt = cast(Any, input_stream).pix_fmt

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
            frame = cast(Any, graph.pull())
            frame.pict_type = "NONE"  # type: ignore[assignment,unused-ignore]
            output_container.mux(cast(Any, output_stream).encode(frame))

        for packet in cast(Any, output_stream).encode():
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
            time_base = input_stream.time_base
            if time_base is not None and (
                float(input_stream.duration * time_base) <= max_segment_duration
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
                output_stream = _add_stream_from_template(
                    output_container, input_stream
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
