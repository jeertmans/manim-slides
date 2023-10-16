"""Additional animations for Manim objects.

Like with Manim, animations are classes that must be put inside a
:meth:`Scene.play<manim.scene.scene.Scene.play>` call.

For each of the provided classes, there exists a method variant
that directly calls :python:`self.play(Animation(...))`, see
:class:`Slide`.
"""

from typing import Any, Mapping, Sequence

import numpy as np

from . import MANIM

if MANIM:
    from manim import LEFT, AnimationGroup, FadeIn, FadeOut, Mobject
else:
    from manimlib import LEFT, AnimationGroup, FadeIn, FadeOut, Mobject


class Wipe(AnimationGroup):  # type: ignore[misc]
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

    .. manim-slides:: WipeClassExample

        from manim import *
        from manim_slides import Slide
        from manim_slides.slide.animation import Wipe

        class WipeClassExample(Slide):
            def construct(self):
                circle = Circle(radius=3, color=BLUE)
                square = Square()

                self.play(FadeIn(circle))
                self.next_slide()

                self.play(Wipe(circle, square))
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


class Zoom(AnimationGroup):  # type: ignore[misc]
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

    .. manim-slides:: ZoomClassExample

        from manim import *
        from manim_slides import Slide
        from manim_slides.slide.animation import Zoom

        class ZoomClassExample(Slide):
            def construct(self):
                circles = [Circle(radius=i) for i in range(1, 4)]

                self.play(FadeIn(circles[0]))
                self.next_slide()

                for i in range(3):
                    self.play(Zoom(circles[i], circles[i+1]))
                    self.next_slide()
    """

    def __init__(
        self,
        current: Sequence[Mobject] = [],
        future: Sequence[Mobject] = [],
        scale: float = 4.0,
        out: bool = False,
        fade_in_kwargs: Mapping[str, Any] = {},
        fade_out_kwargs: Mapping[str, Any] = {},
        **kwargs: Any,
    ) -> None:
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
