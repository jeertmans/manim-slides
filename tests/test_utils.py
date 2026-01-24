from pathlib import Path
from typing import Any

from manim_slides.utils import merge_basenames


def test_add_stream_from_template_with_fallback() -> None:
    class DummyOutputContainer:
        def __init__(self) -> None:
            self.last_add_stream_args: tuple[str, int | None] | None = None

        def add_stream_from_template(self, template: Any) -> None:
            raise TypeError("Template not supported")

        def add_stream(self, codec_name: str, rate: int | None = None) -> "DummyStream":
            self.last_add_stream_args = (codec_name, rate)
            return DummyStream()

    class DummyStream:
        width: int | None = None
        height: int | None = None
        pix_fmt: str | None = None
        time_base: str | None = None
        sample_aspect_ratio: str | None = None

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

        return utils._add_stream_from_template(container, template_stream)

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
