# Examples

Contents of `example.py`.

Do not forget to import Manim Slides and Manim or ManimGL:

```python
from manim import *
from manim_slides import Slide, ThreeDSlide
```

or

```python
from manimlib import *
from manim_slides import Slide, ThreeDSlide
```

Then, each presentation, named `SCENE`, was generated with those two commands:

```bash
manim example.py SCENE # or manimgl example SCENE
manim-slides convert SCENE scene.html -ccontrols=true
```

where `-ccontrols=true` indicates that we want to display the blue navigation arrows.

## Basic Example

Basic example from quickstart.

```{eval-rst}
.. manim-slides: ../../../example.py:BasicExample
    :hide_source:
    :quality: high

.. literalinclude:: ../../../example.py
   :language: python
   :linenos:
   :pyobject: BasicExample
```

## 3D Example

Example using 3D camera. As Manim and ManimGL handle 3D differently, definitions are slightly different.

<div style="position:relative;padding-bottom:56.25%;"> <iframe style="width:100%;height:100%;position:absolute;left:0px;top:0px;" frameborder="0" width="100%" height="100%" allowfullscreen allow="autoplay" src="../_static/three_d_example.html"></iframe></div>

### With Manim

```{eval-rst}
.. literalinclude:: ../../../example.py
   :language: python
   :linenos:
   :dedent: 4
   :start-after: [manim-3d]
   :end-before: [manim-3d]
```

### With ManimGL

```{eval-rst}
.. literalinclude:: ../../../example.py
   :language: python
   :linenos:
   :dedent: 4
   :start-after: [manimgl-3d]
   :end-before: [manimgl-3d]
```

## Subclass Custom Scenes

For compatibility reasons, Manim Slides only provides subclasses for
`Scene` and `ThreeDScene`.
However, subclassing other scene classes is totally possible,
and very simple to do actually!

[For example](https://github.com/jeertmans/manim-slides/discussions/185),
you can subclass the `MovingCameraScene` class from `manim`
with the following code:

```{code-block} python
:linenos:

from manim import *
from manim_slides import Slide


class MovingCameraSlide(Slide, MovingCameraScene):
    pass
```

And later use this class anywhere in your code:


```{code-block} python
:linenos:

class SubclassExample(MovingCameraSlide):
    def construct(self):
        eq1 = MathTex("x", "=", "1")
        eq2 = MathTex("x", "=", "2")

        self.play(Write(eq1))

        self.next_slide()

        self.play(
            TransformMatchingTex(eq1, eq2),
            self.camera.frame.animate.scale(0.5)
        )

        self.wait()
```

:::{note}
If you do not plan to reuse `MovingCameraSlide` more than once, then you can
directly write the `construct` method in the body of `MovingCameraSlide`.
:::

## Advanced Example

A more advanced example is `ConvertExample`, which is used as demo slide and tutorial.

<div style="position:relative;padding-bottom:56.25%;"> <iframe style="width:100%;height:100%;position:absolute;left:0px;top:0px;" frameborder="0" width="100%" height="100%" allowfullscreen allow="autoplay" src="../_static/slides.html"></iframe></div>

```{eval-rst}
.. literalinclude:: ../../../example.py
   :language: python
   :linenos:
   :pyobject: ConvertExample
```
