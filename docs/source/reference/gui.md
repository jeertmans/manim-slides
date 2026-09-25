# Graphical User Interface

Manim Slides' graphical user interface (GUI) is the *de facto* way to present slides.

If you do not specify one of the commands listed in the
[CLI reference](/reference/cli),
Manim Slides will use **present** by default, which launches a GUI window,
playing your scene(s) like so:

```bash
manim-slides [present] [SCENES]...
```

Some optional parameters can be specified and can be listed with:

```bash
manim-slides present --help
```

:::{note}
All the `SCENES` must be in the same folder (`--folder DIRECTORY`), which
defaults to `./slides`. If you rendered your animations without changing
directory, you should not worry about that :-)
:::

## Configuration File

It is possible to configure Manim Slides via a configuration file. You may
initialize the default (local) configuration file with:

```bash
manim-slides init
```

Configuration files are looked up in the following locations, listed by
increasing order of precedence:

1. the global configuration file, e.g., `~/.config/manim-slides/manim-slides.toml`
   on Linux (see [platformdirs](https://platformdirs.readthedocs.io/) for
   other operating systems);
2. a local `.manim-slides.toml` file in the current directory, or any of its
   parent directories (stopping at the filesystem boundary), where the file
   closest to the current directory wins.

This means that you can, e.g., set global defaults for all your presentations,
and override them locally for a specific project.

:::{warning}
Note that, by default, Manim Slides will use default key bindings that are
platform-dependent. If you decide to overwrite those with a config file, you may
encounter some problems from platform to platform.
:::

### Setting Command-Line Defaults

The configuration file can also define default values for command-line options,
using the `[defaults.<command>]` sections, e.g.:

```toml
# .manim-slides.toml
[defaults.present]
full_screen = true

[defaults.convert]
one_file = true
offline = true
```

With the above configuration, running `manim-slides present` will start in
full screen mode, and `manim-slides convert Slide slide.html` will generate
a single, offline, HTML file — without needing to pass any option.

Options passed on the command line always take precedence over the values
from configuration files.

Use `manim-slides checkhealth` to list the configuration files that were
found on your system.

## Configuring Key Bindings

If you wish to use other key bindings than the defaults, you can run the
configuration wizard with:

```bash
manim-slides wizard
```

A similar window to the image below will pop up and prompt to change keys.

```{eval-rst}
.. image:: ../_static/wizard_light.png
    :width: 300px
    :align: center
    :class: only-light
    :alt: Manim Slide Wizard
```

```{eval-rst}
.. image:: ../_static/wizard_dark.png
    :width: 300px
    :align: center
    :class: only-dark
    :alt: Manim Slide Wizard
```

:::{note}
Even though it is not currently supported through the GUI, you can select
multiple key binding for the same action by modifying the config file.
:::
