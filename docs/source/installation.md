# Installation

<!-- start install -->

While installing Manim Slides and its dependencies on your global Python is fine,
we recommend using a virtual environment
(e.g., [venv](https://docs.python.org/3/tutorial/venv.html)) for a local installation.

### Dependencies

<!-- start deps -->

Manim Slides requires either Manim or ManimGL to be installed.
Having both packages installed is fine too.

If none of those packages are installed, please refer to their specific installation guidelines:
- [Manim](https://docs.manim.community/en/stable/installation.html)
- [ManimGL](https://3b1b.github.io/manim/getting_started/installation.html)

:::{warning}
If you install Manim from its git repository, as suggested by ManimGL,
make sure to first check out a supported version (e.g., `git checkout tags/v1.6.1`
for ManimGL), otherwise it might install an unsupported version of Manim!
See [#314](https://github.com/jeertmans/manim-slides/issues/314) for an example.
:::

<!-- end deps -->

### Pip Install

:::{note}
For an easy and safe installation, use [`pipx`](https://pipx.pypa.io/)
instead of `pip`.
:::

The recommended way to install the latest release is to use pip:

```bash
pipx install manim-slides
```

Optionally, you can also install Manim or ManimGL using extras[^1]:

```bash
pip install "manim-slides[manim]"   # For Manim
# or
pip install "manim-slides[manimgl]" # For ManimGL
```

[^1]: You still need to have Manim or ManimGL platform-specific dependencies
  installed on your computer.

### Install From Repository

An alternative way to install Manim Slides is to clone the git repository,
and install from there: read the
[contributing guide](https://eertmans.be/manim-slides/contributing/workflow.html)
to know how to process.

<!-- end install -->
