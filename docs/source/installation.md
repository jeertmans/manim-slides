# Installation

While installing Manim Slides and its dependencies on your global Python is fine,
we recommend using a virtual environment
(e.g., [venv](https://docs.python.org/3/tutorial/venv.html)) for a local installation.

Therefore, the following documentation will install Manim Slides using
[pipx](https://pipx.pypa.io/). This tool is a drop-in replacement
for installing Python packages that ship with one or more executable.

The benefit of using pipx is that it will automatically create a new virtual
environment for every package you install.

:::{note}
Everytime you read `pipx install`, you can use `pip install` instead,
if you are working in a virtual environment or else.
:::

## Dependencies

Manim Slides requires either Manim or ManimGL to be installed, along
with their dependencies.
Having both packages installed is fine too.

If none of those packages are installed,
please refer to their specific installation guidelines:
- [Manim](https://docs.manim.community/en/stable/installation.html)
- [ManimGL](https://3b1b.github.io/manim/getting_started/installation.html)

:::{warning}
If you install Manim from its git repository, as suggested by ManimGL,
make sure to first check out a supported version (e.g., `git checkout tags/v1.6.1`
for ManimGL), otherwise it might install an unsupported version of Manim!
See [#314](https://github.com/jeertmans/manim-slides/issues/314).

Also, note that ManimGL uses outdated dependencies, and may
not work out-of-the-box. One example is NumPy: ManimGL
does not specify any restriction on this package, but
only `numpy<1.25` will work, see
[#2053](https://github.com/3b1b/manim/issues/2053).
:::

## Full Installation

The recommended way to install the latest release
with all features is to use pipx:

```bash
pipx install -U "manim-slides[full]"
```

:::{tip}
While not necessary, the `-U` indicates that we would
like to upgrade to the latest version available,
if Manim Slides is already installed.
:::

:::{note}
The quotes `"` are added because not all shell support unquoted
brackets (e.g., zsh) or commas (e.g., Windows).
:::

You can check that Manim Slides was correctly installed with:

```bash
manim-slides --version
```

## Custom Installation

If you want more control on what dependencies are installed,
you can always install the bare minimal dependencies with:

```bash
pipx install -U manim-slides
```

And install additional dependencies later.

Optionally, you can also install Manim or ManimGL using extras[^1]:

```bash
pipx install -U "manim-slides[manim]"   # For Manim
# or
pipx install -U "manim-slides[manimgl]" # For ManimGL
```

For optional dependencies documentation, see
[next section](#optional-dependencies).

:::{warning}
If you are installing with pipx, this is mandatory to at least include
either `manim` or `manimgl`.
:::

[^1]: You still need to have Manim or ManimGL platform-specific dependencies
  installed on your computer.

## Optional Dependencies

Along with the optional dependencies for Manim and ManimGL,
Manim Slides offers additional *extras*, that can be activated
using optional dependencies:

- `full`, to include `magic`, `manim`, `manimgl`, and
  `sphinx-directive` extras (see below);
- `magic`, to include a Jupyter magic to render
  animations inside notebooks. This automatically installs `manim`,
  and does not work with ManimGL;
- `manim` and `manimgl`, for installing the corresponding
  dependencies;
- `pyqt6` to include PyQt6 Qt bindings. Those bindings are available
  on most platforms and Python version, but produce a weird black
  screen between slide with `manim-slides present`,
  see [#QTBUG-118501](qt-bug-url);
- `pyqt6-full` to include `full` and `pyqt6`;
- `pyside6` to include PySide6 Qt bindings. Those bindings are available
  on most platforms and Python version, except on Python 3.12[^2]; 
- `pyside6-full` to include `full` and `pyside6`;
- `sphinx-directive`, to generate presentation inside your Sphinx
  documentation. This automatically installs `manim`,
  and does not work with ManimGL.

Installing those extras can be done with the following syntax:

```bash
pipx install -U "manim-slides[extra1,extra2]"
```

[qt-bug-url]: https://bugreports.qt.io/browse/QTBUG-118501

[^2]: Actually, PySide6 can be installed on Python 3.12, but you will then
  observe the same visual bug as with PyQt6.

## Install From Repository

An alternative way to install Manim Slides is to clone the git repository,
and install from there: read the
[contributing guide](./contributing/workflow)
to know how to process.
