from __future__ import annotations

from pathlib import Path
from typing import Any, Optional, cast

from manim_slides.utils import merge_basenames


def test_add_stream_from_template_with_fallback() -> None:
    class DummyOutputContainer:
        def __init__(self) -> None:
            self.last_add_stream_args: Optional[tuple[str, Optional[int]]] = None  # noqa: UP045

        def add_stream_from_template(self, template: Any) -> None:
            raise TypeError("Template not supported")

        def add_stream(
            self,
            codec_name: str,
            rate: Optional[int] = None,  # noqa: UP045
        ) -> DummyStream:
            self.last_add_stream_args = (codec_name, rate)
            return DummyStream()

    class DummyStream:
        width: Optional[int] = None  # noqa: UP045
        height: Optional[int] = None  # noqa: UP045
        pix_fmt: Optional[str] = None  # noqa: UP045
        time_base: Optional[str] = None  # noqa: UP045
        sample_aspect_ratio: Optional[str] = None  # noqa: UP045

    class DummyCodecContext:
        name = "libx264"

    class DummyTemplateStream:
        type = "video"
        codec_context = DummyCodecContext()
        codec = None
        average_rate = 24
        base_rate = None
        rate = None
        width = 1920
        height = 1080
        pix_fmt = "yuv420p"
        time_base = "1/24"
        sample_aspect_ratio = "1:1"

    container = DummyOutputContainer()

    def _fake_add_stream_from_template(
        container: DummyOutputContainer, template_stream: DummyTemplateStream
    ) -> DummyStream:
        from manim_slides import utils

        return cast(
            DummyStream,
            utils._add_stream_from_template(
                cast(Any, container),
                cast(Any, template_stream),
            ),
        )

    output_stream = _fake_add_stream_from_template(container, DummyTemplateStream())

    assert container.last_add_stream_args == ("libx264", 24)
    assert output_stream.width == 1920
    assert output_stream.height == 1080
    assert output_stream.pix_fmt == "yuv420p"
    assert output_stream.time_base == "1/24"
    assert output_stream.sample_aspect_ratio == "1:1"


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
