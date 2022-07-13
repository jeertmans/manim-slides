from manim import *

from manim_slides import Slide, ThreeDSlide


class Example(Slide):
    def construct(self):
        circle = Circle(radius=3, color=BLUE)
        dot = Dot()

        self.play(GrowFromCenter(circle))
        self.pause()

        self.start_loop()
        self.play(MoveAlongPath(dot, circle), run_time=2, rate_func=linear)
        self.end_loop()

        self.play(dot.animate.move_to(ORIGIN))
        self.pause()

        self.play(dot.animate.move_to(RIGHT * 3))
        self.pause()

        self.start_loop()
        self.play(MoveAlongPath(dot, circle), run_time=2, rate_func=linear)
        self.end_loop()

        # Each slide MUST end with an animation (a self.wait is considered an animation)
        self.play(dot.animate.move_to(ORIGIN))


class ThreeDExample(ThreeDSlide):
    def construct(self):
        axes = ThreeDAxes()
        circle = Circle(radius=3, color=BLUE)
        dot = Dot(color=RED)

        self.add(axes)

        self.set_camera_orientation(phi=75 * DEGREES, theta=30 * DEGREES)

        self.play(GrowFromCenter(circle))
        self.begin_ambient_camera_rotation(rate=75 * DEGREES / 4)

        self.pause()

        self.start_loop()
        self.play(MoveAlongPath(dot, circle), run_time=4, rate_func=linear)
        self.end_loop()

        self.stop_ambient_camera_rotation()
        self.move_camera(phi=75 * DEGREES, theta=30 * DEGREES)

        self.play(dot.animate.move_to(ORIGIN))
        self.pause()

        self.play(dot.animate.move_to(RIGHT * 3))
        self.pause()

        self.start_loop()
        self.play(MoveAlongPath(dot, circle), run_time=2, rate_func=linear)
        self.end_loop()

        # Each slide MUST end with an animation (a self.wait is considered an animation)
        self.play(dot.animate.move_to(ORIGIN))
