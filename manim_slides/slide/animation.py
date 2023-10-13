"""Additional animations for Manim objects."""

from typing import Any, Mapping, Sequence

import numpy as np

from . import MANIM

if MANIM:
    from manim import LEFT, AnimationGroup, FadeIn, FadeOut, Mobject
else:
    from manimlib import LEFT, AnimationGroup, FadeIn, FadeOut, Mobject


class Wipe(AnimationGroup):
    """
    Creates a wipe animation that will shift all the current objects and future objects
    by a given value.

    :param current: A sequence of mobjects to remove from the scene.
    :param future: A sequence of mobjects to add to the scene.
    :param shift: The shift vector, used for both fading in and out.
    :param fade_in_kwargs: Keyword arguments passed to
        :class:`FadeIn<manim.animation.fading.FadeIn>`.
    :param fade_out_kwargs: Keyword arguments passed to
        :class:`FadeOut<manim.animation.fading.FadeOut>`.
    :param kwargs: Keyword arguments passed to
        :class:`AnimationGroup<manim.animation.composition.AnimationGroup>`.

    Examples
    --------

    .. manim-slides:: WipeExample

        from manim import *
        from manim_slides import Slide

        class WipeExample(Slide):
            def construct(self):
                circle = Circle(radius=3, color=BLUE)
                square = Square()
                text = Text("This is a wipe example").next_to(square, DOWN)
                beautiful = Text("Beautiful, no?")

                self.play(FadeIn(circle))
                self.next_slide()

                self.wipe(circle, Group(square, text))
                self.next_slide()

                self.wipe(Group(square, text), beautiful, direction=UP)
                self.next_slide()

                self.wipe(beautiful, circle, direction=DOWN + RIGHT)
    """

    def __init__(
        self,
        current: Sequence[Mobject] = [],
        future: Sequence[Mobject] = [],
        shift: np.ndarray = LEFT,
        fade_in_kwargs: Mapping[str, Any] = {},
        fade_out_kwargs: Mapping[str, Any] = {},
        **kwargs: Any,
    ):
        animations = []

        for mobject in future:
            animations.append(FadeIn(mobject, shift=shift, **fade_in_kwargs))

        for mobject in current:
            animations.append(FadeOut(mobject, shift=shift, **fade_out_kwargs))

        super().__init__(*animations, **kwargs)


class Zoom(AnimationGroup):
    """
    Creates a zoom animation that will fade out all the current objects, and fade in all
    the future objects. Objects are faded in a direction that goes towards the camera.

    :param current: A sequence of mobjects to remove from the scene.
    :param future: A sequence of mobjects to add to the scene.
    :param scale: How much the objects are scaled (up or down).
    :param out: If set, the objects fade in the opposite direction.
    :param fade_in_kwargs: Keyword arguments passed to
        :class:`FadeIn<manim.animation.fading.FadeIn>`.
    :param fade_out_kwargs: Keyword arguments passed to
        :class:`FadeOut<manim.animation.fading.FadeOut>`.
    :param kwargs: Keyword arguments passed to
        :class:`AnimationGroup<manim.animation.composition.AnimationGroup>`.

    Examples
    --------

    .. manim-slides:: ZoomExample

        from manim import *
        from manim_slides import Slide

        class ZoomExample(Slide):
            def construct(self):
                circle = Circle(radius=3, color=BLUE)
                square = Square()

                self.play(FadeIn(circle))
                self.next_slide()

                self.zoom(circle, square)
                self.next_slide()

                self.zoom(square, circle, out=True, scale=10.0)
    """

    def zoom(
        self,
        current: Sequence[Mobject] = [],
        future: Sequence[Mobject] = [],
        scale: float = 4.0,
        out: bool = False,
        fade_in_kwargs: Mapping[str, Any] = {},
        fade_out_kwargs: Mapping[str, Any] = {},
        **kwargs: Any,
    ) -> AnimationGroup:
        scale_in = 1.0 / scale
        scale_out = scale

        if out:
            scale_in, scale_out = scale_out, scale_in

        animations = []

        for mobject in future:
            animations.append(FadeIn(mobject, scale=scale_in, **fade_in_kwargs))

        for mobject in current:
            animations.append(FadeOut(mobject, scale=scale_out, **fade_out_kwargs))

        super().__init__(*animations, **kwargs)
