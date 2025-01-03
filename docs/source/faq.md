# Frequently Asked Questions

This page summarizes a few of the most frequently asked questions
when using Manim Slides.

They are organized by topic.

If your question is not here, please first look through the
[open **and closed** issues on GitHub](https://github.com/jeertmans/manim-slides/issues?q=is%3Aissue)
or within the [discussions](https://github.com/jeertmans/manim-slides/discussions).

If you still cannot find help after that, do not hesitate to create
your own issue or discussion on GitHub!

## Installing

Everything related to installing Manim-Slides.

Please do not forget the carefully read through
the [installation](/installation) page!

## Rendering

Questions related to `manim-slides render [SCENES]...`,

### I cannot render with ManimGL

ManimGL support is only guaranteed to work
on a very minimal set of versions, because it differs quite a lot from ManimCE,
and its development is not very active.

The typical issue is that ManimGL `<1.7.1` needs an outdated NumPy version, but
can be resolved by manually downgrading NumPy, or upgrading ManimGL (**recommended**).

### Presenting

Questions related to `manim-slides present [SCENES]...`,
or `manim-slides [SCENES]...` for short.

### Can I have interactive slides

No. Slides are pre-rendered static videos files
and cannot be modified on the fly.

If you need new to have some kind of interactive, look
at the preview feature coupled with the OpenGL renderer
with ManimCE or ManimGL.

### Slides go black when video finishes

This is an issue with Qt,
which cannot be solved on all platforms and Python versions,
see [#293](https://github.com/jeertmans/manim-slides/issues/293).

Recent version of Manim Slides, i.e., `manim-slides>5.1.7`, come
with a fix that should work fine.

### How to increase quality on Windows

On Windows platform, one may encounter a lower image resolution than expected.
Usually, this is observed because Windows rescales every application to
fit the screen.
As found by [@arashash](https://github.com/arashash),
in [#20](https://github.com/jeertmans/manim-slides/issues/20),
the problem can be addressed by changing the scaling factor to 100%:

<p align="center">
  <img
    alt="Windows Fix Scaling"
    src="https://raw.githubusercontent.com/jeertmans/manim-slides/main/static/windows_quality_fix.png"
  >
</p>

in *Settings*->*Display*.

## Converting to any format

Questions that apply to all output formats when using
`manim-slides convert [SCENES]...`.

### What are all possible configuration options

Configuration options can be specified with the syntax
`-c<option_name>=<option_value>`.

To list all accepted options, use `manim-slides convert --to=FORMAT --show-config`,
where `FORMAT` is one of the supported formats.
This will also show the default value for each option.

### How to retrieve the current template

If you want to create your own template, the best is to start from the default one.

You can either download it from the
[template folder](https://github.com/jeertmans/manim-slides/tree/main/manim_slides/templates)
or use the `manim-slides convert --to=FORMAT --show-template` command,
where `FORMAT` is one of the supported formats.

## Converting to HTML

Questions related to `manim-slides convert [SCENES]... output.html`.

### I moved my `.html` file and it stopped working

If you did not specify `--one-file` (or `-cone_file=true`) when converting,
then Manim Slides generated a folder containing all
the video files, in the same folder as the HTML
output. As the path to video files is a relative path,
you need to move the HTML **and its assets** altogether.

## Converting to PPTX

Questions related to `manim-slides convert [SCENES]... output.pptx`.

### My media stop playing after a few slides

This issue is (probably) caused by PowerPoint never freeing
memory, causing memory allocation errors, and can be partially
solved by reducing the video quality or the number of slides,
see [#392](https://github.com/jeertmans/manim-slides/issues/392).

Another solution, suggested by [@Azercoco](https://github.com/Azercoco) in
[#392 (comment)](https://github.com/jeertmans/manim-slides/issues/392#issuecomment-2368198106),
is to disable hardware/GPU acceleration.
