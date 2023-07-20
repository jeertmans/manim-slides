# Application Programming Interface

Manim Slides' API is very limited: it simply consists of two classes, `Slide` and `ThreeDSlide`, which are subclasses of `Scene` and `ThreeDScene` from Manim.

Therefore, we only document here the methods we think the end-user will ever use, not the methods used internally when rendering.

```{eval-rst}
.. autoclass:: manim_slides.Slide
    :members:
        add_to_canvas,
        canvas,
        canvas_mobjects,
        end_loop,
        mobjects_without_canvas,
        next_slide,
        pause,
        remove_from_canvas,
        start_loop,
        wait_time_between_slides,
        wipe,

.. autoclass:: manim_slides.ThreeDSlide
    :members:
```
