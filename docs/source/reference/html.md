# HTML Presentations

Manim Slides allows you to convert presentations into one HTML file, with
[RevealJS](https://revealjs.com/). This file can then be opened with any modern
web browser, allowing for a nice portability of your presentations.

As with every command with Manim Slides, converting slides' fragments into one
HTML file (and its assets) can be done in one command:

```bash
manim-slides convert [SCENES]... DEST
```

where `DEST` is the `.html` destination file.

## Configuring the Template

Many configuration options are available through the `-c<option>=<value>` syntax.
Most, if not all, RevealJS options should be available by default. If that is
not the case, please
[fill an issue](https://github.com/jeertmans/manim-slides/issues/new/choose)
on GitHub.

You can print the list of available options with:

```bash
manim-slides convert --show-config
```

## Using a Custom Template

The default template used for HTML conversion can be found on
[GitHub](https://github.com/jeertmans/manim-slides/blob/main/manim_slides/templates/revealjs.html)
or printed with the `--show-template` option.
If you wish to use another template, you can do so with the
`--use-template FILE` option.

## More about HTML Slides

You can read more about HTML slides in the [sharing](/reference/sharing) section.
