# Customize your RevealJS slides

One of the benefits of the `convert` command is the use of template files.

Currently, only the HTML export uses one. If not specified, the template
will be the one shipped with Manim Slides, see
[`manim_slides/templates/revealjs.html`](https://github.com/jeertmans/manim-slides/blob/main/manim_slides/templates/revealjs.html).

Because you can actually use your own template with  the `--use-template`
option, possibilities are infinite!

## Adding a real-time clock

:::{note}
This example is inspired from
[@gsong-math's comment](https://github.com/jeertmans/manim-slides/issues/356#issuecomment-1902626943)
on Manim Slides' repository.
:::

### What to add

```{eval-rst}
.. literalinclude:: ../_static/template.diff
   :language: html
```

### How it renders

### Full code

```{eval-rst}
.. literalinclude:: ../_static/template.html
   :language: html+jinja
```
