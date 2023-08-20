# flake8: noqa: F403, F405
# type: ignore
import sys

if "manimlin" in sys.modules:
    from manimlib import *

    MANIMGL = True
else:
    from manim import *

    MANIMGL = False

from manim_slides import Slide, ThreeDSlide


class BasicExample(Slide):
    def construct(self):
        circle = Circle(radius=3, color=BLUE)
        dot = Dot()

        self.play(GrowFromCenter(circle))
        self.next_slide()  # Waits user to press continue to go to the next slide

        self.start_loop()  # Start loop
        self.play(MoveAlongPath(dot, circle), run_time=2, rate_func=linear)
        self.end_loop()  # This will loop until user inputs a key

        self.play(dot.animate.move_to(ORIGIN))
        self.next_slide()  # Waits user to press continue to go to the next slide


class MultipleAnimationsInLastSlide(Slide):
    """This is used to check against solution for issue #161."""

    def construct(self):
        circle = Circle(color=BLUE)
        dot = Dot()

        self.play(GrowFromCenter(circle))
        self.play(FadeIn(dot))
        self.next_slide()

        self.play(dot.animate.move_to(RIGHT))
        self.play(dot.animate.move_to(UP))
        self.play(dot.animate.move_to(LEFT))
        self.play(dot.animate.move_to(DOWN))

        self.next_slide()


class TestFileTooLong(Slide):
    """This is used to check against solution for issue #123."""

    def construct(self):
        import random

        circle = Circle(radius=3, color=BLUE)
        dot = Dot()
        self.play(GrowFromCenter(circle), run_time=0.1)

        for _ in range(30):
            direction = (random.random() - 0.5) * LEFT + (random.random() - 0.5) * UP
            self.play(dot.animate.move_to(direction), run_time=0.1)
            self.play(dot.animate.move_to(ORIGIN), run_time=0.1)

        self.next_slide()


class ConvertExample(Slide):
    """WARNING: this example does not seem to work with ManimGL."""

    def construct(self):
        self.wait_time_between_slides = 0.1

        title = VGroup(
            Text("From Manim animations", t2c={"From": BLUE}),
            Text("to slides presentation", t2c={"to": BLUE}),
            Text("with Manim Slides", t2w={"[-12:]": BOLD}, t2c={"[-13:]": YELLOW}),
        ).arrange(DOWN)

        step_1 = Text("1. In your scenes file, import Manim Slides")
        step_2 = Text("2. Replace Scene with Slide")
        step_3 = Text("3. In construct, add pauses where you need")
        step_4 = Text("4. You can also create loops")
        step_5 = Text("5. Render you scene with Manim")
        step_6 = Text("6. Open your presentation with Manim Slides")

        for step in [step_1, step_2, step_3, step_4, step_5, step_6]:
            step.scale(0.5).to_corner(UL)

        step = step_1

        self.play(FadeIn(title))

        self.next_slide()

        code = Code(
            code="""from manim import *


class Example(Scene):
    def construct(self):
        dot = Dot()
        self.add(dot)

        self.play(Indicate(dot, scale_factor=2))

        square = Square()
        self.play(Transform(dot, square))

        self.play(Rotate(square, angle=PI/2))
""",
            language="python",
        )

        code_step_1 = Code(
            code="""from manim import *
from manim_slides import Slide

class Example(Scene):
    def construct(self):
        dot = Dot()
        self.add(dot)

        self.play(Indicate(dot, scale_factor=2))

        square = Square()
        self.play(Transform(dot, square))

        self.play(Rotate(square, angle=PI/2))
""",
            language="python",
        )

        code_step_2 = Code(
            code="""from manim import *
from manim_slides import Slide

class Example(Slide):
    def construct(self):
        dot = Dot()
        self.add(dot)

        self.play(Indicate(dot, scale_factor=2))

        square = Square()
        self.play(Transform(dot, square))

        self.play(Rotate(square, angle=PI/2))
""",
            language="python",
        )

        code_step_3 = Code(
            code="""from manim import *
from manim_slides import Slide

class Example(Slide):
    def construct(self):
        dot = Dot()
        self.add(dot)

        self.play(Indicate(dot, scale_factor=2))
        self.next_slide()
        square = Square()
        self.play(Transform(dot, square))
        self.next_slide()
        self.play(Rotate(square, angle=PI/2))
""",
            language="python",
        )

        code_step_4 = Code(
            code="""from manim import *
from manim_slides import Slide

class Example(Slide):
    def construct(self):
        dot = Dot()
        self.add(dot)
        self.start_loop()
        self.play(Indicate(dot, scale_factor=2))
        self.end_loop()
        square = Square()
        self.play(Transform(dot, square))
        self.next_slide()
        self.play(Rotate(square, angle=PI/2))
""",
            language="python",
        )

        code_step_5 = Code(
            code="manim example.py Example",
            language="console",
        )

        code_step_6 = Code(
            code="manim-slides Example",
            language="console",
        )

        or_text = Text("or generate HTML presentation").scale(0.5)

        code_step_7 = Code(
            code="manim-slides convert Example slides.html --open",
            language="console",
        ).shift(DOWN)

        self.play(self.wipe(title, code))
        self.next_slide()

        self.play(FadeIn(step, shift=RIGHT))
        self.play(Transform(code, code_step_1))
        self.next_slide()

        self.play(Transform(step, step_2))
        self.play(Transform(code, code_step_2))
        self.next_slide()

        self.play(Transform(step, step_3))
        self.play(Transform(code, code_step_3))
        self.next_slide()

        self.play(Transform(step, step_4))
        self.play(Transform(code, code_step_4))
        self.next_slide()

        self.play(Transform(step, step_5))
        self.play(Transform(code, code_step_5))
        self.next_slide()

        self.play(Transform(step, step_6))
        self.play(Transform(code, code_step_6))
        self.play(code.animate.shift(UP), FadeIn(code_step_7), FadeIn(or_text))
        self.next_slide()

        watch_text = Text("Watch result on next slides!").shift(2 * DOWN).scale(0.5)

        self.start_loop()
        self.play(FadeIn(watch_text))
        self.play(FadeOut(watch_text))
        self.end_loop()
        self.clear()

        dot = Dot()
        self.add(dot)
        self.start_loop()
        self.play(Indicate(dot, scale_factor=2))
        self.end_loop()
        square = Square()
        self.play(Transform(dot, square))
        self.remove(dot)
        self.add(square)
        self.next_slide()
        self.play(Rotate(square, angle=PI / 4))
        self.next_slide()

        learn_more_text = (
            VGroup(
                Text("Learn more about Manim Slides:"),
                Text("https://github.com/jeertmans/manim-slides", color=YELLOW),
            )
            .arrange(DOWN)
            .scale(0.75)
        )

        self.play(Transform(square, learn_more_text))


# For ThreeDExample, things are different

if not MANIMGL:
    # [manim-3d]
    class ThreeDExample(ThreeDSlide):
        def construct(self):
            axes = ThreeDAxes()
            circle = Circle(radius=3, color=BLUE)
            dot = Dot(color=RED)

            self.add(axes)

            self.set_camera_orientation(phi=75 * DEGREES, theta=30 * DEGREES)

            self.play(GrowFromCenter(circle))
            self.begin_ambient_camera_rotation(rate=75 * DEGREES / 4)

            self.next_slide()

            self.start_loop()
            self.play(MoveAlongPath(dot, circle), run_time=4, rate_func=linear)
            self.end_loop()

            self.stop_ambient_camera_rotation()
            self.move_camera(phi=75 * DEGREES, theta=30 * DEGREES)

            self.play(dot.animate.move_to(ORIGIN))
            self.next_slide()

            self.play(dot.animate.move_to(RIGHT * 3))
            self.next_slide()

            self.start_loop()
            self.play(MoveAlongPath(dot, circle), run_time=2, rate_func=linear)
            self.end_loop()

            self.play(dot.animate.move_to(ORIGIN))

    # [manim-3d]
else:
    # [manimgl-3d]
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

            def updater(m, dt):
                return m.increment_theta((75 * DEGREES / 4) * dt)

            frame.add_updater(updater)

            self.next_slide()

            self.start_loop()
            self.play(MoveAlongPath(dot, circle), run_time=4, rate_func=linear)
            self.end_loop()

            frame.remove_updater(updater)
            self.play(frame.animate.set_theta(30 * DEGREES))
            self.play(dot.animate.move_to(ORIGIN))
            self.next_slide()

            self.play(dot.animate.move_to(RIGHT * 3))
            self.next_slide()

            self.start_loop()
            self.play(MoveAlongPath(dot, circle), run_time=2, rate_func=linear)
            self.end_loop()

            self.play(dot.animate.move_to(ORIGIN))

    # [manimgl-3d]
