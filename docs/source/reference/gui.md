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

It is possible to configure Manim Slides via a configuration file, even though
this feature is currently limited. You may initialize the default configuration
file with:

```bash
manim-slides init
```

:::{warning}
Note that, by default, Manim Slides will use default key bindings that are
platform-dependent. If you decide to overwrite those with a config file, you may
encounter some problems from platform to platform.
:::

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
