# manim-presentation

Tool for live presentations using [manim](https://www.manim.community/)

## Install

```
pip install manim-presentation opencv-python
```

## Usage

Use the class `Slide` as your scenes base class

```python
from manim_presentation import Slide

class Example(Slide):
    def construct(self):
        ...
```

call `self.pause()` when you want to pause the playback and wait for an input to continue (check the keybindings)

Wrap a series of animations between `self.start_loop()` and `self.stop_loop()` when you want to loop them (until input to continue)

```python
from manim import *
from manim_presentation import Slide

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

You **must** end your `Slide` with a `self.play(...)` or a `self.wait(..)`

To start the presentation using `Scene1`, `Scene2` and so on simply run:

```
manim_presentation Scene1 Scene2...
```

## Default Keybindings

Default keybindings to control the presentation

|  Keybinding |          Action          |
|:-----------:|:------------------------:|
| Right Arrow |    Continue/Next Slide   |
|  Left Arrow |      Previous Slide      |
|      R      | Re-Animate Current Slide |
|   Spacebar  |        Play/Pause        |
|      Q      |           Quit           |


You can specify different keybindings creating a file named `manim-presentation.json` with the keys: `QUIT_KEY` `CONTINUE_KEY` `BACK_KEY` `REWIND_KEY` and `PLAYPAUSE_KEY`
`manim-presentation` uses `cv2.waitKeyEx()` to wait for keypresses

## Run Example

Clone this repository

```
git clone https://github.com/galatolofederico/manim-presentation.git
cd manim-presentation
```

Create a virtualenv

```
virtualenv --python=python3.7 env
. ./env/bin/activate
```

Install `manim` and `manim_presentation`

```
pip install manim manim-presentation opencv-python
```

Render the example scene

```
manim -qh example.py
```

Run the presentation

```
manim_presentation Example
```

## Contributions and license

The code is released as Free Software under the [GNU/GPLv3](https://choosealicense.com/licenses/gpl-3.0/) license. Copying, adapting and republishing it is not only consent but also encouraged. 

For any further question feel free to reach me at  [federico.galatolo@ing.unipi.it](mailto:federico.galatolo@ing.unipi.it) or on Telegram  [@galatolo](https://t.me/galatolo)