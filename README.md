![Manim Slides Logo](https://raw.githubusercontent.com/jeertmans/manim-slides/main/static/logo.png)

[![Latest Release][pypi-version-badge]][pypi-version-url]
[![Python version][pypi-python-version-badge]][pypi-version-url]
![PyPI - Downloads](https://img.shields.io/pypi/dm/manim-slides)
# Manim Slides

Tool for live presentations using either [Manim (community edition)](https://www.manim.community/) or [ManimGL](https://3b1b.github.io/manim/). Manim Slides will *automatically* detect the one you are using!

> **_NOTE:_**  This project extends the work of [`manim-presentation`](https://github.com/galatolofederico/manim-presentation), with a lot more features!

- [Install](#install)
  * [Dependencies](#dependencies)
  * [Pip install](#pip-install)
  * [Install From Repository](#install-from-repository)
- [Usage](#usage)
  * [Basic Example](#basic-example)
  * [Key Bindings](#key-bindings)
  * [Other Examples](#other-examples)
- [Features and Comparison with Original manim-presentation](#features-and-comparison-with-original-manim-presentation)
- [Contributing](#contributing)

## Installation

While installing Manim Slides and its dependencies on your global Python is fine, I recommend using a [virtualenv](https://docs.python.org/3/tutorial/venv.html) for a local installation.

### Dependencies

Manim Slides requires either Manim or ManimGL to be installed. Having both packages installed is fine too.

If none of those packages are installed, please refer to their specifc installation guidelines:
- [Manim](https://docs.manim.community/en/stable/installation.html)
- [ManimGL](https://3b1b.github.io/manim/getting_started/installation.html)

### Pip Install

The recommended way to install the latest release is to use pip:

```bash
pip install manim-slides
```

### Install From Repository

An alternative way to install Manim Slides is to clone the git repository, and install from there:

```bash
git clone https://github.com/jeertmans/manim-slides
pip install -e .
```

> *Note:* the `-e` flag allows you to edit the files, and observe the changes directly when using Manim Slides

## Usage

Using Manim Slides is a two-step process:
1. Render animations using `Slide` (resp. `ThreeDSlide`) as a base class instead of `Scene` (resp. `ThreeDScene`), and add calls to `self.pause()` everytime you want to create a new slide.
2. Run `manim-slides` on rendered animations and display them like a *Power Point* presentation.

### Basic Example


Wrap a series of animations between `self.start_loop()` and `self.stop_loop()` when you want to loop them (until input to continue):

```python
# example.py

from manim import *
# or: from manimlib import *
from manim_slides import Slide

class Example(Slide):
    def construct(self):
        circle = Circle(radius=3, color=BLUE)
        dot = Dot()

        self.play(GrowFromCenter(circle))
        self.pause()  # Waits user to press continue to go to the next slide

        self.start_loop()  # Start loop
        self.play(MoveAlongPath(dot, circle), run_time=2, rate_func=linear)
        self.end_loop()  # This will loop until user inputs a key

        self.play(dot.animate.move_to(ORIGIN))
        self.pause()  # Waits user to press continue to go to the next slide

        self.wait()  # The presentation directly exits after last animation
```

You **must** end your `Slide` with a `self.play(...)` or a `self.wait(...)`.

First, render the animation files:

```bash
manim example.py
# or
manimgl example.py
```

To start the presentation using `Scene1`, `Scene2` and so on simply run:

```bash
manim-slides [OPTIONS] Scene1 Scene2...
```

Or in this example:

```bash
manim-slides Example
```

##  Key Bindings

The default key bindings to control the presentation are:

|  Keybinding |          Action          |
|:-----------:|:------------------------:|
| Right Arrow |    Continue/Next Slide   |
|  Left Arrow |      Previous Slide      |
|      R      |   Replay Current Slide   |
|      V      |   Reverse Current Slide  |
|   Spacebar  |        Play/Pause        |
|      Q      |           Quit           |

You can run the **configuration wizard** to change those key bindings:

```bash
manim-slides wizard
```

Alternatively you can specify different key bindings creating a file named `.manim-slides.json` with the keys: `QUIT` `CONTINUE` `BACK` `REVERSE` `REWIND` and `PLAY_PAUSE`.

A default file can be created with:

```bash
manim-slides init
```

> **_NOTE:_**  `manim-slides` uses `cv2.waitKeyEx()` to wait for keypresses, and directly registers the key code.

## Other Examples

Other examples are available in the [`example.py`](https://github.com/jeertmans/manim-slides/blob/main/example.py) file, if you downloaded the git repository.

Below is a small recording of me playing with the slides back and forth.

![](https://raw.githubusercontent.com/jeertmans/manim-slides/main/static/example.gif)


## Features and Comparison with original manim-presentation

Below is a non-exhaustive list of features:

| Feature | `manim-slides` | `manim-presentation` |
|:--------|:--------------:|:--------------------:|
| Support for Manim | :heavy_check_mark: | :heavy_check_mark: |
| Support for ManimGL | :heavy_check_mark: | :heavy_multiplication_x: |
| Configurable key bindings | :heavy_check_mark: | :heavy_check_mark: |
| Configurable paths | :heavy_check_mark: | :heavy_multiplication_x: |
| Play / Pause slides | :heavy_check_mark: | :heavy_check_mark: |
| Next / Previous slide | :heavy_check_mark: | :heavy_check_mark: |
| Replay slide | :heavy_check_mark: | :heavy_check_mark: |
| Reverse slide | :heavy_check_mark: | :heavy_multiplication_x: |
| Multiple key per actions | :heavy_check_mark: | :heavy_multiplication_x: |
| One command line tool | :heavy_check_mark: | :heavy_multiplication_x: |
| Robust config file parsing | :heavy_check_mark: | :heavy_multiplication_x: |
| Support for 3D Scenes | :heavy_check_mark: | :heavy_multiplication_x: |
| Documented code | :heavy_check_mark: | :heavy_multiplication_x: |
| Tested on Unix, macOS, and Windows | :heavy_check_mark: | :heavy_multiplication_x: |


## Contributing

Contributions are more than welcome!

[pypi-version-badge]: https://img.shields.io/pypi/v/manim-slides?label=manim-slides
[pypi-version-url]: https://pypi.org/project/manim-slides/
[pypi-python-version-badge]: https://img.shields.io/pypi/pyversions/manim-slides
