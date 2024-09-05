# flake8: noqa: F403, F405
# type: ignore

from manim_slides import Slide
from manim_slides.slide import MANIM, MANIMGL

if MANIM:
    from manim import *
elif MANIMGL:
    from manimlib import *


class BasicSlide(Slide):
    def construct(self):
        text = Text("This is some text")

        self.play(Write(text))

        circle = Circle(radius=3, color=BLUE)

        self.play(Transform(text, circle))

        circle = text  # this is to avoid name confusion

        square = Square()

        self.play(FadeIn(square))

        self.next_slide(loop=True)

        self.play(Rotate(square, +PI / 2))
        self.play(Rotate(square, -PI / 2))

        self.next_slide()

        other_text = Text("Other text")
        self.wipe([square, circle], [other_text])

        self.next_slide()
        self.zoom(other_text, [])


class BasicSlideSkipReversing(BasicSlide):
    skip_reversing = True
