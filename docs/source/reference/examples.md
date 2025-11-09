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
.. manim-slides:: ../../../example.py:BasicExample
    :hide_source:
    :quality: high

.. literalinclude:: ../../../example.py
   :language: python
   :linenos:
   :pyobject: BasicExample
```

## 3D Example

Example using 3D camera. As Manim and ManimGL handle 3D differently,
definitions are slightly different.

### With Manim

```{eval-rst}
.. manim-slides:: ../../../example.py:ThreeDExample
    :hide_source:
    :quality: high

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
    """Example taken from ManimCE's docs."""

    def construct(self):
        self.camera.frame.save_state()

        ax = Axes(x_range=[-1, 10], y_range=[-1, 10])
        graph = ax.plot(lambda x: np.sin(x), color=WHITE, x_range=[0, 3 * PI])

        dot_1 = Dot(ax.i2gp(graph.t_min, graph))
        dot_2 = Dot(ax.i2gp(graph.t_max, graph))
        self.add(ax, graph, dot_1, dot_2)

        self.play(self.camera.frame.animate.scale(0.5).move_to(dot_1))
        self.next_slide()
        self.play(self.camera.frame.animate.move_to(dot_2))
        self.next_slide()
        self.play(Restore(self.camera.frame))
        self.wait()
```

:::{note}
If you do not plan to reuse `MovingCameraSlide` more than once, then you can
directly write the `construct` method in the body of `MovingCameraSlide`.
:::

```{eval-rst}
.. manim-slides:: SubclassExample
    :hide_source:
    :quality: high

    from manim import *
    from manim_slides import Slide


    class MovingCameraSlide(Slide, MovingCameraScene):
        pass

    class SubclassExample(MovingCameraSlide):
        def construct(self):
            self.camera.frame.save_state()

            ax = Axes(x_range=[-1, 10], y_range=[-1, 10])
            graph = ax.plot(lambda x: np.sin(x), color=WHITE, x_range=[0, 3 * PI])

            dot_1 = Dot(ax.i2gp(graph.t_min, graph))
            dot_2 = Dot(ax.i2gp(graph.t_max, graph))
            self.add(ax, graph, dot_1, dot_2)

            self.play(self.camera.frame.animate.scale(0.5).move_to(dot_1))
            self.next_slide()
            self.play(self.camera.frame.animate.move_to(dot_2))
            self.next_slide()
            self.play(Restore(self.camera.frame))
            self.wait()
```

## Subsection Example

Example demonstrating the use of subsections within a single slide.

**Key concept**: `next_subsection()` keeps building on existing content (accumulates),
while `next_slide()` starts fresh (clears the screen). This example shows a diagram
being built step by step, with each subsection adding more elements while keeping
everything from previous subsections visible.

```{eval-rst}
.. manim-slides:: ../../../example.py:SubsectionExample
    :hide_source:
    :quality: high

.. literalinclude:: ../../../example.py
   :language: python
   :linenos:
   :pyobject: SubsectionExample
```

This example creates **two slides**:
- **Slide 1**: Title slide showing "Subsections Demo"
- **Slide 2**: Main content with **four subsections**:
  1. First subsection adds a circle
  2. Second subsection adds a square (circle still visible)
  3. Third subsection adds labels (circle and square still visible)
  4. Fourth subsection adds an arrow connecting them (everything still visible)

Note that `auto_next=True` on the third subsection will automatically advance
to the fourth subsection after animations complete.

## Advanced Example

A more advanced example is `ConvertExample`, which is used as demo slide and tutorial.

```{eval-rst}
.. manim-slides:: ../../../example.py:ConvertExample
    :hide_source:
    :quality: high

.. literalinclude:: ../../../example.py
   :language: python
   :linenos:
   :pyobject: ConvertExample
```
