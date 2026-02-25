# HTML Presentations

Manim Slides allows you to convert presentations into one HTML file, with
[RevealJS](https://revealjs.com/). This file can then be opened with any modern
web browser, allowing for a nice portability of your presentations.

As with every command with Manim Slides, converting slides' fragments into one
HTML file (and its assets) can be done in one command:

```bash
manim-slides convert [SCENES]... DEST
```

where `DEST` is the `.html` destination file.

## Configuring the Template

Many configuration options are available through the `-c<option>=<value>` syntax.
Most, if not all, RevealJS options should be available by default. If that is
not the case, please
[fill an issue](https://github.com/jeertmans/manim-slides/issues/new/choose)
on GitHub.

You can print the list of available options with:

```bash
manim-slides convert --show-config
```

## Using a Custom Template

The default template used for HTML conversion can be found on
[GitHub](https://github.com/jeertmans/manim-slides/blob/main/manim_slides/templates/revealjs.html)
or printed with the `--show-template` option.
If you wish to use another template, you can do so with the
`--use-template FILE` option.

## Vertical Slides

Slides default to a "horizontal" arrangement by default. This means that each
slide follows the next in a linear progression. If you instead wish to add
an additional dimension to your slides and have "vertical" groupings under a
given "horizontal" slide, you may pass the keyword argument "direction" to the
{meth}`next_slide<manim_slides.slide.Slide.next_slide>`
method and give it the argument "vertical". The "horizontal" slides
will be the main progression of your presentation accessible by tabbing left
or right using those arrow keys. For "vertical" slides you move to the "horizontal"
parent slide and use the up and down keys to navigate through the slides that are
grouped under the initial slide. You may still use the left/right navigation to
move from any slide in the vertical stack to the next "horizontal" slide.

In the following example we have only the linear "horizontal" slides.
Note that no direction argument is passed to
{meth}`self.next_slide()<manim_slides.slide.Slide.next_slide>`.

```{eval-rst}
.. manim-slides:: HorizontalSlides
    :config_options: slide_number=true

    from manim import *
    from manim_slides import Slide

    class HorizontalSlides(Slide):
        def construct(self):
            circle = Circle(radius=3, color=BLUE)
            dot = Dot()

            self.play(GrowFromCenter(circle))

            self.next_slide(loop=True)
            self.play(MoveAlongPath(dot, circle), run_time=2, rate_func=linear)
            self.next_slide()

            self.play(dot.animate.move_to(ORIGIN))
```

In this example the second slide is a "vertical" slide so the left right progression
moves from slide 1 to slide 3, while to access slide 2 you must be on slide 1 and
press the down key.

```{eval-rst}
.. manim-slides:: VerticalAndHorizontalSlides
    :config_options: slide_number=true

    from manim import *
    from manim_slides import Slide

    class VerticalAndHorizontalSlides(Slide):
        def construct(self):
            circle = Circle(radius=3, color=BLUE)
            dot = Dot()

            self.play(GrowFromCenter(circle))

            self.next_slide(direction="vertical", loop=True)
            self.play(MoveAlongPath(dot, circle), run_time=2, rate_func=linear)
            self.next_slide(direction="vertical")

            self.play(dot.animate.move_to(ORIGIN))
```

For more information about vertical slides see <https://revealjs.com/vertical-slides/>.

## More about HTML Slides

You can read more about HTML slides in the [sharing](/reference/sharing) section.
