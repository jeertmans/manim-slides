# type: ignore

from manim_slides import Slide, ThreeDSlide
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


class FailingSlide(Slide):
    def construct(self):
        self.play("this fails to render")


class Issue540(ThreeDSlide):
    def construct(self):
        k = ValueTracker(0)

        def slice_function(x, y):
            return x + y

        def z_slice(num):
            k.set_value(num)
            return ImplicitFunction(
                slice_function, color=YELLOW, x_range=((-5, 5)), y_range=((-5, 5))
            )

        ref_dot2 = always_redraw(
            lambda: Dot3D(
                point=interpolate(
                    DOWN,
                    UP,
                    k.get_value(),
                ),
            )
        )

        slice = z_slice(1)
        self.play(
            FadeIn(slice),
            run_time=0.025,
        )

        self.play(FadeOut(ref_dot2))

