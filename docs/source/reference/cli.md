# Command Line Interface

This page contains an exhaustive list of all the commands available with `manim-slides`.


```{eval-rst}
.. click:: manim_slides.__main__:cli
    :prog: manim-slides
    :nested: full
```

## All config options

Each converter has its own configuration options, which are listed below.

::::{dropdown} HTML
```{program-output} manim-slides convert --to=html --show-config
```
::::

::::{dropdown} Zip
:::{note}
The Zip converter inherits from the HTML converter.
:::
```{program-output} manim-slides convert --to=zip --show-config
```
::::

::::{dropdown} PDF
```{program-output} manim-slides convert --to=pdf --show-config
```
::::

::::{dropdown} HTML
```{program-output} manim-slides convert --to=pdf --show-config
```
::::
