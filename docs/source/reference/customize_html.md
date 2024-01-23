# Customize your RevealJS slides

One of the benefits of the `convert` command is the use of template files.

Currently, only the HTML export uses one. If not specified, the template
will be the one shipped with Manim Slides, see
[`manim_slides/templates/revealjs.html`](https://github.com/jeertmans/manim-slides/blob/main/manim_slides/templates/revealjs.html).

Because you can actually use your own template with  the `--use-template`
option, possibilities are infinite!

:::{warning}
Currently, the `PresentationConfig` class and its components
are not part of the public API. You can still use them, e.g.,
in the templates, but you may expect breaking changes between
releases.

Eventually, this will become part of the public API too,
and we will document its usage.
:::

## Adding a clock to each slide

In this example, we show how to add a self-updating clock
to the bottom left corner of every slide.

:::{note}
This example is inspired from
[@gsong-math's comment](https://github.com/jeertmans/manim-slides/issues/356#issuecomment-1902626943)
on Manim Slides' repository.
:::

### What to add

Whenever you want to create a template, it is best practice
to start from the default one (see link above).

Modifying it needs very basic HTML/JavaScript/CSS skills.
To add a clock, you can simply add the following to the
default template file:

```{eval-rst}
.. literalinclude:: ../_static/template.diff
   :language: html
```

:::{tip}
Because we use RevealJS to generate HTML slides,
we recommend you to take a look at
[RevealJS' documentation](https://revealjs.com/).
:::

### How it renders

Then, using the `:template: <path/to/custom_template.html>`
option, the basic example renders as follows:

```{eval-rst}
.. manim-slides:: ../../../example.py:BasicExample
    :hide_source:
    :template: ../_static/template.html
```

### Full code

Below, you can read the full content of the template file.

```{eval-rst}
.. literalinclude:: ../_static/template.html
   :language: html+jinja
```
