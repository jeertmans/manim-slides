> [!IMPORTANT]
> Take the [**Manim Slides Survey**](https://forms.gle/i4scrwPQghbTQwQs5)
> to help improve this tool! Thanks in advance to all the people taking the time
> to answer this short survey! The form is open until **January 31st 2025**,
> and results will be communicated in the GitHub discussions.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jeertmans/manim-slides/main/static/logo_dark_transparent.png">
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/jeertmans/manim-slides/main/static/logo_light_transparent.png">
  <img alt="Manim Slides Logo" src="https://raw.githubusercontent.com/jeertmans/manim-slides/main/static/logo.png">
</picture>

<!-- start pypi -->

[![Latest Release][pypi-version-badge]][pypi-version-url]
[![Python version][pypi-python-version-badge]][pypi-version-url]
[![PyPI - Downloads][pypi-download-badge]][pypi-version-url]
[![Documentation][documentation-badge]][documentation-url]
[![DOI][doi-badge]][doi-url]
[![JOSE Paper][jose-badge]][jose-url]
[![codecov][codecov-badge]][codecov-url]
[![Binder][binder-badge]][binder-url]

# Manim Slides

Tool for live presentations using either
[Manim (community edition)](https://www.manim.community/)
or [ManimGL](https://3b1b.github.io/manim/).
Manim Slides will *automatically* detect the one you are using!

> [!NOTE]
> This project extends the work of
> [`manim-presentation`](https://github.com/galatolofederico/manim-presentation),
> with a lot more features!

- [Installation](#installation)
- [Usage](#usage)
- [Comparison with Similar Tools](#comparison-with-similar-tools)
- [F.A.Q](https://eertmans.be/manim-slides/latest/faq.html)
- [Citing](#citing)
- [Contributing](#contributing)
  * [Reporting an Issue](#reporting-an-issue)
  * [Seeking for Help](#seeking-for-help)
  * [Contact](#contact)

## Installation

Manim Slides requires either Manim or ManimGL to be installed, along
with their dependencies. Please checkout the
[documentation](https://eertmans.be/manim-slides/latest/installation.html)
for detailed install instructions.

## Usage

<!-- start usage -->

Using Manim Slides is a two-step process:
1. Render animations using `Slide` (resp. `ThreeDSlide`) as a base class instead
   of `Scene` (resp. `ThreeDScene`), and add calls to `self.next_slide()`
   every time you want to create a new slide.
2. Run `manim-slides` on rendered animations and display them like a
   *PowerPoint* presentation.

The documentation is available [online](https://eertmans.be/manim-slides/).

### Basic Example

Call `self.next_slide()` every time you want to create a pause between
animations, and `self.next_slide(loop=True)` if you want the next slide to loop
over animations until the user presses continue:

```python
from manim import *  # or: from manimlib import *

from manim_slides import Slide


class BasicExample(Slide):
    def construct(self):
        circle = Circle(radius=3, color=BLUE)
        dot = Dot()

        self.play(GrowFromCenter(circle))
        self.next_slide()  # Waits user to press continue to go to the next slide

        self.next_slide(loop=True)  # Start loop
        self.play(MoveAlongPath(dot, circle), run_time=2, rate_func=linear)
        self.next_slide()  # This will start a new non-looping slide

        self.play(dot.animate.move_to(ORIGIN))
```

First, render the animation files:

```bash
manim-slides render example.py BasicExample
# or use ManimGL
manim-slides render --GL example.py BasicExample
```
<!-- end usage -->

> [!NOTE]
> Using `manim-slides render` makes sure to use the `manim`
> (or `manimlib`) library that was installed in the same Python environment.
> Put simply, this is a wrapper around
> `manim render [ARGS]...` (or `manimgl [ARGS]...`).

<!-- start more-usage -->

To start the presentation using `Scene1`, `Scene2` and so on, run:

```bash
manim-slides [OPTIONS] Scene1 Scene2...
```

In our example:

```bash
manim-slides BasicExample
```

<!-- end more-usage -->

<p align="center">
  <img alt="Example GIF" src="https://raw.githubusercontent.com/jeertmans/manim-slides/main/static/example.gif">
</p>

For detailed usage documentation, run `manim-slides --help`, or go to the
[documentation](https://eertmans.be/manim-slides/latest/reference/cli.html).

## Interactive Tutorial

Click on the image to watch a slides presentation that explains to you how
to use Manim Slides.

[![Manim Slides Docs](https://raw.githubusercontent.com/jeertmans/manim-slides/main/static/docs.png)](https://eertmans.be/manim-slides/)

## More Examples

More examples are available in the
[`example.py`](https://github.com/jeertmans/manim-slides/blob/main/example.py)
file, if you downloaded the git repository.

## Comparison with Similar Tools

There exists a variety of tools that allows to create slides presentations
containing Manim animations.

Below is a comparison of the most used ones with Manim Slides:

| Project name | Manim Slides | Manim Presentation | Manim Editor | Jupyter Notebooks |
|:------------:|:------------:|:------------------:|:------------:|:-----------------:|
| Link | [![GitHub Repo stars](https://img.shields.io/github/stars/jeertmans/manim-slides?style=social)](https://github.com/jeertmans/manim-slides) | [![GitHub Repo stars](https://img.shields.io/github/stars/galatolofederico/manim-presentation?style=social)](https://github.com/galatolofederico/manim-presentation) | [![GitHub Repo stars](https://img.shields.io/github/stars/ManimCommunity/manim_editor?style=social)](https://github.com/ManimCommunity/manim_editor) | [![GitHub Repo stars](https://img.shields.io/github/stars/jupyter/notebook?style=social)](https://github.com/jupyter/notebook) |
| Activity | [![GitHub Repo stars](https://img.shields.io/github/last-commit/jeertmans/manim-slides?style=social)](https://github.com/jeertmans/manim-slides) | [![GitHub Repo stars](https://img.shields.io/github/last-commit/galatolofederico/manim-presentation?style=social)](https://github.com/galatolofederico/manim-presentation) | [![GitHub Repo stars](https://img.shields.io/github/last-commit/ManimCommunity/manim_editor?style=social)](https://github.com/ManimCommunity/manim_editor) | [![GitHub Repo stars](https://img.shields.io/github/last-commit/jupyter/notebook?style=social)](https://github.com/jupyter/notebook) |
| Usage | Command-line | Command-line | Web Browser | Notebook |
| Note | Requires minimal modif. in scenes files | Requires minimal modif. in scenes files |  Requires the usage of sections, and configuration through graphical interface | Relies on `nbconvert` to create slides from a Notebook |
| Support for ManimGL | Yes | No | No | No |
| Web Browser presentations | Yes | No | Yes | No |
| Offline presentations | Yes, with Qt | Yes, with OpenCV | No | No

## Citing

If you use this project, please cite it using the following reference:

```bibtex
@article{Jerome_Eertmans_Manim_Slides_A_2023,
	title        = {{Manim Slides: A Python package for presenting Manim content anywhere}},
	author       = {{Jérome Eertmans}},
	year         = 2023,
	month        = aug,
	journal      = {Journal of Open Source Education},
	volume       = 6,
	doi          = {10.21105/jose.00206}
}
```

or by linking this GitHub repository at the end of the presentation.

## Contributing

Contributions are more than welcome! Please read through
[our contributing section](https://eertmans.be/manim-slides/latest/contributing/index.html).

### Reporting an Issue

<!-- start reporting-an-issue -->

If you think you found a bug,
an error in the documentation,
or wish there was some feature that is currently missing,
we would love to hear from you!

The best way to reach us is via the
[GitHub issues](https://github.com/jeertmans/manim-slides/issues).
If your problem is not covered by an already existing (closed or open) issue,
then we suggest you create a
[new issue](https://github.com/jeertmans/manim-slides/issues/new/choose).
You can choose from a list of templates, or open a
[blank issue](https://github.com/jeertmans/manim-slides/issues/new)
if your issue does not fit one of the proposed topics.

The more precise you are in the description of your problem, the faster we will
be able to help you!

<!-- end reporting-an-issue -->

### Seeking for help

<!-- start seeking-for-help -->

Sometimes, you may have a question about Manim Slides,
not necessarily an issue.

First, make sure to read the
[F.A.Q](https://eertmans.be/manim-slides/latest/faq.html) to see if
your question has already been answered. If not, please follow the
recommendation (from that page) to reach us for questions.

<!-- end seeking-for-help -->

### Contact

<!-- start contact -->

Finally, if you do not have any GitHub account,
or just wish to contact the author of Manim Slides,
you can do so at: [jeertmans@icloud.com](mailto:jeertmans@icloud.com).

<!-- end contact -->

[pypi-version-badge]: https://img.shields.io/pypi/v/manim-slides?label=manim-slides
[pypi-version-url]: https://pypi.org/project/manim-slides/
[pypi-python-version-badge]: https://img.shields.io/pypi/pyversions/manim-slides
[pypi-download-badge]: https://img.shields.io/pypi/dm/manim-slides
[documentation-badge]: https://readthedocs.org/projects/manim-slides/badge/?version=latest
[documentation-url]: https://manim-slides.readthedocs.io/
[doi-badge]: https://zenodo.org/badge/DOI/10.5281/zenodo.8215167.svg
[doi-url]: https://doi.org/10.5281/zenodo.8215167
[jose-badge]: https://jose.theoj.org/papers/10.21105/jose.00206/status.svg
[jose-url]: https://doi.org/10.21105/jose.00206
[codecov-badge]: https://codecov.io/gh/jeertmans/manim-slides/branch/main/graph/badge.svg?token=8P4DY9JCE4
[codecov-url]: https://codecov.io/gh/jeertmans/manim-slides
[binder-badge]: https://mybinder.org/badge_logo.svg
[binder-url]: https://mybinder.org/v2/gh/jeertmans/manim-slides-binder/HEAD?filepath=getting_started.ipynb
