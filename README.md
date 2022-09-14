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

|  Keybinding |          Action          | Icon |
|:-----------:|:------------------------:|:----:|
| Right Arrow |    Continue/Next Slide   | <svg height="25px" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 512"><!--! Font Awesome Pro 6.2.0 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license (Commercial License) Copyright 2022 Fonticons, Inc. --><path d="M52.5 440.6c-9.5 7.9-22.8 9.7-34.1 4.4S0 428.4 0 416V96C0 83.6 7.2 72.3 18.4 67s24.5-3.6 34.1 4.4l192 160L256 241V96c0-17.7 14.3-32 32-32s32 14.3 32 32V416c0 17.7-14.3 32-32 32s-32-14.3-32-32V271l-11.5 9.6-192 160z"/></svg> |
|  Left Arrow |      Previous Slide      | <svg height="25px" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 512"><!--! Font Awesome Pro 6.2.0 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license (Commercial License) Copyright 2022 Fonticons, Inc. --><path d="M267.5 440.6c9.5 7.9 22.8 9.7 34.1 4.4s18.4-16.6 18.4-29V96c0-12.4-7.2-23.7-18.4-29s-24.5-3.6-34.1 4.4l-192 160L64 241V96c0-17.7-14.3-32-32-32S0 78.3 0 96V416c0 17.7 14.3 32 32 32s32-14.3 32-32V271l11.5 9.6 192 160z"/></svg> |
|      R      |   Replay Current Slide   | <svg height="25px" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><!--! Font Awesome Pro 6.2.0 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license (Commercial License) Copyright 2022 Fonticons, Inc. --><path d="M48.5 224H40c-13.3 0-24-10.7-24-24V72c0-9.7 5.8-18.5 14.8-22.2s19.3-1.7 26.2 5.2L98.6 96.6c87.6-86.5 228.7-86.2 315.8 1c87.5 87.5 87.5 229.3 0 316.8s-229.3 87.5-316.8 0c-12.5-12.5-12.5-32.8 0-45.3s32.8-12.5 45.3 0c62.5 62.5 163.8 62.5 226.3 0s62.5-163.8 0-226.3c-62.2-62.2-162.7-62.5-225.3-1L185 183c6.9 6.9 8.9 17.2 5.2 26.2s-12.5 14.8-22.2 14.8H48.5z"/></svg> |
|      V      |   Reverse Current Slide  | <svg height="25px" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><!--! Font Awesome Pro 6.2.0 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license (Commercial License) Copyright 2022 Fonticons, Inc. --><path d="M459.5 440.6c9.5 7.9 22.8 9.7 34.1 4.4s18.4-16.6 18.4-29V96c0-12.4-7.2-23.7-18.4-29s-24.5-3.6-34.1 4.4L288 214.3V256v41.7L459.5 440.6zM256 352V256 128 96c0-12.4-7.2-23.7-18.4-29s-24.5-3.6-34.1 4.4l-192 160C4.2 237.5 0 246.5 0 256s4.2 18.5 11.5 24.6l192 160c9.5 7.9 22.8 9.7 34.1 4.4s18.4-16.6 18.4-29V352z"/></svg> |
|   Spacebar  |        Play/Pause        | <svg height="25px" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 384 512"><!--! Font Awesome Pro 6.2.0 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license (Commercial License) Copyright 2022 Fonticons, Inc. --><path d="M73 39c-14.8-9.1-33.4-9.4-48.5-.9S0 62.6 0 80V432c0 17.4 9.4 33.4 24.5 41.9s33.7 8.1 48.5-.9L361 297c14.3-8.7 23-24.2 23-41s-8.7-32.2-23-41L73 39z"/></svg> <svg height="25px" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 512"><!--! Font Awesome Pro 6.2.0 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license (Commercial License) Copyright 2022 Fonticons, Inc. --><path d="M48 64C21.5 64 0 85.5 0 112V400c0 26.5 21.5 48 48 48H80c26.5 0 48-21.5 48-48V112c0-26.5-21.5-48-48-48H48zm192 0c-26.5 0-48 21.5-48 48V400c0 26.5 21.5 48 48 48h32c26.5 0 48-21.5 48-48V112c0-26.5-21.5-48-48-48H240z"/></svg> |
|      Q      |           Quit           | <svg height="25px" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 512"><!--! Font Awesome Pro 6.2.0 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license (Commercial License) Copyright 2022 Fonticons, Inc. --><path d="M310.6 150.6c12.5-12.5 12.5-32.8 0-45.3s-32.8-12.5-45.3 0L160 210.7 54.6 105.4c-12.5-12.5-32.8-12.5-45.3 0s-12.5 32.8 0 45.3L114.7 256 9.4 361.4c-12.5 12.5-12.5 32.8 0 45.3s32.8 12.5 45.3 0L160 301.3 265.4 406.6c12.5 12.5 32.8 12.5 45.3 0s12.5-32.8 0-45.3L205.3 256 310.6 150.6z"/></svg> |

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
| Documented code | WIP | :heavy_multiplication_x: |
| Tested on Unix, macOS, and Windows | :heavy_check_mark: | :heavy_multiplication_x: |


## Contributing

Contributions are more than welcome!

[pypi-version-badge]: https://img.shields.io/pypi/v/manim-slides?label=manim-slides
[pypi-version-url]: https://pypi.org/project/manim-slides/
[pypi-python-version-badge]: https://img.shields.io/pypi/pyversions/manim-slides
