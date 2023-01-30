# Examples

Contents of `example.py`.

Do not forget to import Manim Slides and Manim or ManimGL.

## Basic Example

Basic example from quickstart.

<div style="position:relative;padding-bottom:56.25%;"> <iframe style="width:100%;height:100%;position:absolute;left:0px;top:0px;" frameborder="0" width="100%" height="100%" allowfullscreen allow="autoplay" src="../_static/basic_example.html"></iframe></div>

```{eval-rst}
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

## Advanced Example

A more advanced example is `ConvertExample`, which is used as demo slide and tutorial.

<div style="position:relative;padding-bottom:56.25%;"> <iframe style="width:100%;height:100%;position:absolute;left:0px;top:0px;" frameborder="0" width="100%" height="100%" allowfullscreen allow="autoplay" src="../_static/slides.html"></iframe></div>

```{eval-rst}
.. literalinclude:: ../../../example.py
   :language: python
   :linenos:
   :pyobject: ConvertExample
```
