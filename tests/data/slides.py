# flake8: noqa: F403, F405
# type: ignore
from manim import *

from manim_slides import Slide


class BasicSlide(Slide):
    def construct(self):
        circle = Circle(radius=3, color=BLUE)
        dot = Dot()

        self.play(GrowFromCenter(circle))
        self.next_slide()

        self.start_loop()
        self.play(MoveAlongPath(dot, circle), run_time=2, rate_func=linear)
        self.wait(2.0)
        self.end_loop()

        self.play(dot.animate.move_to(ORIGIN))
        self.next_slide()

        self.play(self.wipe(Group(dot, circle), []))
