# Application Programming Interface

Manim Slides' API is very limited: it simply consists of two classes, `Slide`
and `ThreeDSlide`, which are subclasses of `Scene` and `ThreeDScene` from Manim.

Therefore, we only document here the methods we think the end-user will ever
use, not the methods used internally when rendering.

## Slide

```{eval-rst}
.. autoclass:: manim_slides.slide.Slide
    :members:
        add_to_canvas,
        canvas,
        canvas_mobjects,
        mobjects_without_canvas,
        next_section,
        next_slide,
        remove_from_canvas,
        wait_time_between_slides,
        wipe,
        zoom,
```

## 3D Slide

```{eval-rst}
.. autoclass:: manim_slides.slide.ThreeDSlide
    :members:
```

## Animations

```{eval-rst}
.. automodule:: manim_slides.slide.animation
    :members:
        Wipe,
        Zoom,
```
