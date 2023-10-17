# Features Table

The following summarizes the different presentation features Manim Slides offers.

:::{table} Comparison of the different presentation methods.
:widths: auto
:align: center

| Feature / Constraint | [`present`](reference/cli.md) | [`convert --to=html`](reference/cli.md) | [`convert --to=pptx`](reference/cli.md) | [`convert --to=pdf`](reference/cli.md)
| :--- | :---: | :---: | :---: | :---: |
| Basic navigation through slides | Yes | Yes | Yes | Yes (static image) |
| Replay slide | Yes | No | No | N/A |
| Pause animation | Yes | No | No | N/A |
| Play slide in reverse | Yes | No | No | N/A |
| Slide count | Yes | Yes (optional) | Yes (optional) | N/A |
| Needs Python with Manim Slides installed | Yes | No | No | No
| Requires internet access | No | Yes | No | No |
| Auto. play slides | Yes | Yes | Yes | N/A |
| Loops support | Yes | Yes | Yes | N/A |
| Fully customizable | No | Yes (`--use-template` option) | No | No |
| Other dependencies | None | A modern web browser | PowerPoint or LibreOffice Impress[^1] | None |
| Works cross-platforms | Yes | Yes | Partly[^1][^2] | Yes |
:::

[^1]: If you encounter a problem where slides do not automatically play or loops do not work,
  please
  [file an issue on GitHub](https://github.com/jeertmans/manim-slides/issues/new/choose).
[^2]: PowerPoint online does not seem to support automatic playing of videos,
  so you need LibreOffice Impress on Linux platforms.
