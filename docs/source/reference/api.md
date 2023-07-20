# Application Programming Interface

Manim Slides' API is very limited: it simply consists of two classes, `Slide` and `ThreeDSlide`, which are subclasses of `Scene` and `ThreeDScene` from Manim.

Therefore, we only document here the methods we think the end-user will ever use, not the methods used internally when rendering.

```{eval-rst}
.. autoclass:: manim_slides.Slide
    :members: wait_time_between_slides, start_loop, end_loop, pause, next_slide, wipe

.. autoclass:: manim_slides.ThreeDSlide
    :members:
```
