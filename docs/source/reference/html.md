# HTML Presentations

Manim Slides provides two HTML exporters:

- `--to=html` is the existing [RevealJS](https://revealjs.com/) exporter. It
  remains the default for an `.html` destination and supports RevealJS templates
  and configuration.
- `--to=html-player` uses the dependency-free Manim Slides player. It supports
  generated reverse media, replay, touch input, and completely self-contained
  offline output.

As with every command with Manim Slides, converting slides' fragments into one
HTML file (and its assets) can be done in one command:

```bash
manim-slides convert [SCENES]... DEST
```

where `DEST` is the `.html` destination file. Automatic format detection chooses
RevealJS; select the first-party player explicitly:

```bash
manim-slides convert BasicExample presentation.html --to=html-player
```

## First-party HTML player

The default player output is one HTML file plus a `presentation_assets`
directory. The directory contains the local runtime and collision-safe copies of
every forward and reverse media asset. Keep it beside the HTML file when moving
or publishing the presentation. The output makes no CDN or telemetry requests.

For a single portable file, add `--one-file`:

```bash
manim-slides convert BasicExample presentation.html --to=html-player --one-file
```

The portable file contains the manifest, player, styles, and media. It can be
opened directly by double-clicking it (`file://`); no local server or internet
connection is needed. Media is decoded lazily into Blob URLs, with a bounded
working set. Portable files are approximately one third larger than their raw
binary media because of Base64 encoding, and the current and nearby decoded
assets require additional browser memory. Prefer asset-backed output for large
decks or web hosting.

### Playback and controls

The player loads the replacement media and its target frame before displaying
it. Backward navigation plays the generated reverse clip. When reversing a
partly played forward clip, equal-duration media starts at the corresponding
reverse time. If durations differ by more than 15%, the deterministic fallback
plays the reverse clip from its beginning.

Keyboard and presentation-remote controls are:

| Input | Action |
| :--- | :--- |
| Space, Right, Page Down | Advance |
| Left, Page Up | Go backward |
| R | Replay the current forward animation |
| P | Pause or resume at the configured playback rate |
| N | Toggle safely rendered notes |
| O | Toggle the compact overview; selecting a slide jumps to its held end frame |
| F | Toggle fullscreen when the browser supports it |
| ? | Show help |
| Escape | Close overlays or leave fullscreen |

A primary click or tap on the presentation advances. A horizontal swipe moves
forward or backward. An upward swipe enters a following vertical slide, and a
downward swipe leaves the current vertical slide. Each gesture dispatches at
most one navigation command.

Browsers may reject playback until the user interacts with the page, especially
when externally supplied media contains audio. The player then shows a clear
play button and remains paused instead of claiming to be playing. With
`prefers-reduced-motion: reduce`, animations remain paused on their starting
frame until the viewer chooses **Play animation** or explicitly replays them;
navigation, notes, and direct jumps remain available.

### Browser, accessibility, and embedding notes

The player targets current desktop and mobile browsers with Blob URLs,
`playsinline`, and standard HTML media support. Chromium is the required tested
baseline. Actual codec support is browser- and operating-system-dependent; an
unsupported or missing asset produces a slide- and role-specific error with
retry and navigation controls.

Controls are semantic buttons with visible keyboard focus and 44 CSS-pixel touch
targets. Viewport sizing uses dynamic viewport units and safe-area insets. The
player's CSS and input listeners are scoped to its root. In an embedded host,
keyboard events are handled only while the player or one of its controls has
focus, and pointer handling does not originate outside the player.

The generated CSS class names and DOM structure are implementation details, not
a compatibility API. For durable custom layout, place the generated file in a
responsive `iframe`, or override only the outer `.manim-slides-player` size in a
host integration and test it against the Manim Slides versions you support.

Image slides use their static image for both logical directions. `loop`,
`auto_next`, forward and reverse playback rates, notes, direction, multiple
scenes, resolution, and background color come from the existing slide metadata.

## Configuring the RevealJS template

Many configuration options are available through the `-c<option>=<value>` syntax.
Most, if not all, RevealJS options should be available by default. If that is
not the case, please
[fill an issue](https://github.com/jeertmans/manim-slides/issues/new/choose)
on GitHub.

You can print the list of available options with:

```bash
manim-slides convert --show-config
```

## Using a Custom RevealJS template

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
