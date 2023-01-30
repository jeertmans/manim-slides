# Application Programming Interface

Manim Slides' API is very limited: it simply consists in two classes, `Slide` and `ThreeDSlide`, which are subclasses of `Scene` and `ThreeDScene` from Manim.

Thefore, we only document here the methods we think the end-user will ever use, not the methods used internally when rendering.

```{eval-rst}
.. autoclass:: manim_slides.Slide
    :members: start_loop, end_loop, pause, play

.. autoclass:: manim_slides.ThreeDSlide
    :members:
```
