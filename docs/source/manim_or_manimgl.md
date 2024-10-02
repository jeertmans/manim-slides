# Manim or ManimGL

Manim Slides supports both Manim (Community Edition) and ManimGL (by 3b1b).

Because both modules have slightly different APIs, Manim Slides needs to know
which Manim API you are using, to import the correct module.

## Default Behavior

By default, Manim Slides looks at {py:data}`sys.modules` and chooses the first
Manim package that is already imported: `manim` for Manim,
`manimlib` for ManimGL. This works pretty well when rendering
the slides.

If both modules are present in {py:data}`sys.modules`, then Manim Slides will
prefer using `manim`.

### Usage

The simplest way to use Manim Slides with the correct Manim API is to:

1. first import the Manim API;
2. and, then, import `manim_slides`.

Example for `manim`:

```python
from manim import *
from manim_slides import Slide
```

Example for `manimlib`:

```python
from manimlib import *
from manim_slides import Slide
```

### Example of Default Import

The following code shows how Manim Slides detected that `manimlib`
was imported, so the {py:class}`Slide<manim_slides.slide.Slide>`
automatically subclasses the class from ManimGL, not Manim.

```python
from manimlib import Scene
from manim_slides import Slide

assert issubclass(Slide, Scene)  # Slide subclasses Scene from ManimGL

from manim import Scene

assert not issubclass(Slide, Scene)  # but not Scene from Manim
```

## Custom Manim API

If you want to override the default Manim API, you can set the `MANIM_API`
environment variable to:

- `manim` or `manimce` to import `manim`;
- `manimlib` or `manimgl` to import `manimlib`;

prior to importing `manim_slides`.

Note that Manim Slides will still first look at {py:data}`sys.modules` to check
if any of the two modules is already imported.

If you want to force Manim Slides to obey the `MANIM_API` environment variable,
you must also set `FORCE_MANIM_API=1`.
