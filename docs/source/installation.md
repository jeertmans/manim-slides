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
Every time you read `pipx install`, you can use `pip install` instead,
if you are working in a virtual environment or else.
:::

## Dependencies

<!-- start deps -->

Manim Slides requires either Manim or ManimGL to be installed, along
with their dependencies.
Having both packages installed is fine too.

If none of those packages are installed,
please refer to their specific installation guidelines:
- [Manim](https://docs.manim.community/en/stable/installation.html)
- [ManimGL](https://3b1b.github.io/manim/getting_started/installation.html)

<!-- end deps -->

## Pip Install

The recommended way to install the latest release
with all features is to use pipx:

```bash
pipx install -U "manim-slides[pyside6-full]"
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

## Custom install

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

## Optional dependencies

Along with the optional dependencies for Manim and ManimGL,
Manim Slides offers additional *extras*, that can be activated
using optional dependencies:

- `full`, to include `magic`, `manim`, and
  `sphinx-directive` extras (see below);
- `magic`, to include a Jupyter magic to render
  animations inside notebooks. This automatically installs `manim`,
  and does not work with ManimGL;
- `manim` and `manimgl`, for installing the corresponding
  dependencies;
- `pyqt6` to include PyQt6 Qt bindings;
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

[^2]: Actually, PySide6 can be installed on Python 3.12, but you will then
  observe the same visual bug as with PyQt6.

## Nixpkgs installation

Manim Slides is distributed under Nixpkgs >=24.05.
If you are using Nix or NixOS, you can find Manim Slides under:

 - `nixpkgs.manim-slides`, which is meant to be a stand alone application and
   includes PyQt6 (see above);
 - `nixpkgs.python3Packages.manim-slides`, which is meant to be used as a
   module (for notebook magics), and includes IPython but does not include
   any Qt binding.

You can try out the Manim Slides package with:

```sh
nix-shell -p manim ffmpeg manim-slides
```

or by adding it to your
[configuration file](https://nixos.org/manual/nixos/stable/#sec-package-management).

Alternatively, you can try Manim Slides in a Python environment with:

```sh
nix-shell -p manim ffmpeg "python3.withPackages(ps: with ps; [ manim-slides, ...])"
```

or bundle this into [your Nix environment](https://wiki.nixos.org/wiki/Python).

:::{note}
Nix does not currently support `manimgl`.
:::

## When you need a Qt backend

Before `v5.1`, Manim Slides automatically included PySide6 as
a Qt backend. As only `manim-slides present` and `manim-slides wizard`
command need a graphical library, and installing PySide6 on all platforms
and Python version can be sometimes complicated, Manim Slides chooses
**not to include** any Qt backend.

The use can choose between PySide6 (best) and PyQt6, depending on their
availability and licensing rules.

As of `v5.1`, you **need** to have Qt bindings installed to use
`manim-slides present` or `manim-slides wizard`. The recommended way to
install those are via optional dependencies, as explained above.

## Install from source

An alternative way to install Manim Slides is to clone the git repository,
and build the package from source. Read the
[contributing guide](/contributing/workflow)
to know how to process.
