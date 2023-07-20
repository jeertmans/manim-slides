import pytest
from manim import Text
from pydantic import ValidationError

from manim_slides.slide import Slide


def assert_construct(cls: type) -> type:
    class Wrapper:
        @classmethod
        def test_construct(_) -> None:
            cls().construct()

    return Wrapper


class TestSlide:
    @assert_construct
    class TestLoop(Slide):
        def construct(self) -> None:
            text = Text("Some text")

            self.add(text)

            self.start_loop()
            self.play(text.animate.scale(2))
            self.end_loop()

            with pytest.raises(AssertionError):
                self.end_loop()

            self.start_loop()
            with pytest.raises(AssertionError):
                self.start_loop()

            with pytest.raises(ValidationError):
                self.end_loop()

    @assert_construct
    class TestWipe(Slide):
        def construct(self) -> None:
            text = Text("Some text")
            bye = Text("Bye")

            self.add(text)

            assert text in self.mobjects
            assert bye not in self.mobjects

            self.play(self.wipe([text], [bye]))

            assert text not in self.mobjects
            assert bye in self.mobjects

    @assert_construct
    class TestCanvas(Slide):
        def construct(self) -> None:
            text = Text("Some text")
            bye = Text("Bye")

            assert len(self.canvas) == 0

            self.add(text)

            assert len(self.canvas) == 0

            self.add_to_canvas(text=text)

            assert len(self.canvas) == 1

            self.add(bye)

            assert len(self.canvas) == 1

            assert text not in self.mobjects_without_canvas
            assert bye in self.mobjects_without_canvas

            self.remove(text)

            assert len(self.canvas) == 1

            self.add_to_canvas(bye=bye)

            assert len(self.canvas) == 2

            self.remove_from_canvas("text", "bye")

            assert len(self.canvas) == 0

            with pytest.raises(KeyError):
                self.remove_from_canvas("text")
