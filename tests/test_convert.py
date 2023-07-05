import pytest

from manim_slides.convert import PDF, Converter, PowerPoint, RevealJS


class TestConverter:
    @pytest.mark.parametrize(
        ("name", "converter"), [("html", RevealJS), ("pdf", PDF), ("pptx", PowerPoint)]
    )
    def test_from_string(self, name: str, converter: type) -> None:
        assert Converter.from_string(name) == converter
