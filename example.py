# flake8: noqa: F403, F405
# type: ignore
import sys

if "manim" in sys.modules:
    from manim import *

    MANIMGL = False
elif "manimlib" in sys.modules:
    from manimlib import *

    MANIMGL = True
else:
    raise ImportError("This script must be run with either `manim` or `manimgl`")

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


# For ThreeDExample, things are different

if not MANIMGL:

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

else:
    # WARNING: 3b1b's manim change how ThreeDScene work,
    # this is why things have to be managed differently.
    class ThreeDExample(Slide):
        CONFIG = {
            "camera_class": ThreeDCamera,
        }

        def construct(self):
            axes = ThreeDAxes()
            circle = Circle(radius=3, color=BLUE)
            dot = Dot(color=RED)

            self.add(axes)

            frame = self.camera.frame
            frame.set_euler_angles(
                theta=30 * DEGREES,
                phi=75 * DEGREES,
                gamma=0,
            )

            self.play(GrowFromCenter(circle))
            updater = lambda m, dt: m.increment_theta((75 * DEGREES / 4) * dt)
            frame.add_updater(updater)

            self.pause()

            self.start_loop()
            self.play(MoveAlongPath(dot, circle), run_time=4, rate_func=linear)
            self.end_loop()

            frame.remove_updater(updater)
            self.play(frame.animate.set_theta(30 * DEGREES))
            self.play(dot.animate.move_to(ORIGIN))
            self.pause()

            self.play(dot.animate.move_to(RIGHT * 3))
            self.pause()

            self.start_loop()
            self.play(MoveAlongPath(dot, circle), run_time=2, rate_func=linear)
            self.end_loop()

            # Each slide MUST end with an animation (a self.wait is considered an animation)
            self.play(dot.animate.move_to(ORIGIN))
