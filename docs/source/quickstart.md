# Quickstart

If not already, install Manim Slides, along with either Manim or ManimGL,
see [installation](/installation).

## Creating your first slides

```{include} ../../README.md
:start-after: <!-- start usage -->
:end-before: <!-- end usage -->
```

:::{note}
Using `manim-slides render` makes sure to use the `manim`
(or `manimlib`) library that was installed in the same Python environment.
Put simply, this is a wrapper around
`manim render [ARGS]...` (or `manimgl [ARGS]...`).
:::


```{include} ../../README.md
:start-after: <!-- start more-usage -->
:end-before: <!-- end more-usage -->
```

The output slides should look this this:

```{eval-rst}
.. manim-slides:: ../../example.py:BasicExample
    :hide_source:
    :quality: high
```

For more advanced examples,
see the [Examples](/reference/examples) section.
