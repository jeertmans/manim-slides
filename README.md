[![Latest Release][pypi-version-badge]][pypi-version-url]
[![Python version][pypi-python-version-badge]][pypi-version-url]
![PyPI - Downloads](https://img.shields.io/pypi/dm/manim-slides)
# Manim Slides

Tool for live presentations using either [manim-community](https://www.manim.community/) or [manimgl](https://3b1b.github.io/manim/). `manim-slides` will automatically detect the one you are using!

> **_NOTE:_**  This project extends the work of [`manim-presentation`](https://github.com/galatolofederico/manim-presentation), with a lot more features!

## Install

```
pip install manim-slides
```

## Usage

Use the class `Slide` as your scenes base class:
```python
from manim_slides import Slide

class Example(Slide):
    def construct(self):
        ...
```

call `self.pause()` when you want to pause the playback and wait for an input to continue (check the keybindings).

Wrap a series of animations between `self.start_loop()` and `self.stop_loop()` when you want to loop them (until input to continue):
```python
from manim import *
# or: from manimlib import *
from manim_slides import Slide

class Example(Slide):
    def construct(self):
        circle = Circle(radius=3, color=BLUE)
        dot = Dot()

        self.play(GrowFromCenter(circle))
        self.pause()

        self.start_loop()
        self.play(MoveAlongPath(dot, circle), run_time=2, rate_func=linear)
        self.end_loop()

        self.play(dot.animate.move_to(ORIGIN))
        self.pause()

        self.wait()
```

You **must** end your `Slide` with a `self.play(...)` or a `self.wait(..)`.

To start the presentation using `Scene1`, `Scene2` and so on simply run:
```
manim-slides Scene1 Scene2...
```

##  Keybindings

Default keybindings to control the presentation:

|  Keybinding |          Action          |
|:-----------:|:------------------------:|
| Right Arrow |    Continue/Next Slide   |
|  Left Arrow |      Previous Slide      |
|      R      | Re-Animate Current Slide |
|      V      |   Reverse Current Slide  |
|   Spacebar  |        Play/Pause        |
|      Q      |           Quit           |


You can run the **configuration wizard** with:

```
manim-slides wizard
```

Alternatively you can specify different keybindings creating a file named `.manim-slides.json` with the keys: `QUIT` `CONTINUE` `BACK` `REVERSE` `REWIND` and `PLAY_PAUSE`.

A default file can be created with:
```
manim-slides init
```

> **_NOTE:_**  `manim-slides` uses `cv2.waitKeyEx()` to wait for keypresses, and directly registers the key code.

## Run Example

Clone this repository:
```
git clone https://github.com/jeertmans/manim-slides.git
cd manim-slides
```

Install `manim` and `manim-slides`:
```
pip install manim manim-slides
# or
pip install manimgl manim-slides
```

Render the example scene:
```
manim -qh example.py Example
# or
manimgl --hd example.py Example
```

Run the presentation
```
manim-slides Example
```

Below is a small recording of me playing with the slides back and forth.

![](https://raw.githubusercontent.com/jeertmans/manim-slides/main/static/example.gif)


## Comparison with original `manim-presentation`

Here are a few things that I implemented (or that I'm planning to implement) on top of the original work:

- [x] Allowing multiple keys to control one action (useful when you use a laser pointer)
- [x] More robust config files checking
- [x] Dependencies are installed with the package
- [x] Only one cli (to rule them all)
- [x] User can easily generate dummy config file
- [x] Config file path can be manually set
- [x] Play animation in reverse [#9](https://github.com/galatolofederico/manim-presentation/issues/9)
- [x] Handle 3D scenes out of the box
- [x] Support for both `manim` and `manimgl` modules
- [ ] Generate docs online
- [x] Fix the quality problem on Windows platforms with `fullscreen` flag

## Contributions and license

The code is released as Free Software under the [GNU/GPLv3](https://choosealicense.com/licenses/gpl-3.0/) license. Copying, adapting and republishing it is not only consent but also encouraged.

[pypi-version-badge]: https://img.shields.io/pypi/v/manim-slides?label=manim-slides
[pypi-version-url]: https://pypi.org/project/manim-slides/
[pypi-python-version-badge]: https://img.shields.io/pypi/pyversions/manim-slides
