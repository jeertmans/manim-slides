# Workflow

This document is there to help you recreate a working environment for Manim Slides.

## Dependencies

```{include} ../installation.md
:start-after: <!-- start deps -->
:end-before: <!-- end deps -->
```

## Forking the repository and cloning it locally

We use GitHub to host Manim Slides' repository, and we encourage contributors to use git.

Useful links:

* [GitHub's Hello World](https://docs.github.com/en/get-started/quickstart/hello-world).
* [GitHub Pull Request in 100 Seconds](https://www.youtube.com/watch?v=8lGpZkjnkt4&ab_channel=Fireship).

Once you feel comfortable with git and GitHub,
[fork](https://github.com/jeertmans/manim-slides/fork)
the repository, and clone it locally.

As for every Python project, using virtual environment is recommended to avoid
conflicts between modules.
For this project, we use [uv](https://github.com/astral-sh/uv) to easily manage project
and development dependencies. If not already, please install this tool.

## Installing Python modules

With uv, installation becomes straightforward:

```bash
uv sync --all-extras
```

:::{note}
You still need the same dependencies as to install Manim and ManimGL,
so please check their respective installation guides.
:::

## Running commands

Because modules are installed in a new Python environment,
you cannot use them directly in the shell.
Instead, you either need to prepend `uv run` to any command, e.g.:

```bash
uv run manim-slides wizard
```

## Testing your code

Most of the tests are done with GitHub actions, thus not on your computer.
The only command you should run locally is:

```bash
uv run pre-commit run --all-files
```

This runs a few linter and formatter to make sure the code quality and style stay
constant across time.
If a warning or an error is displayed, please fix it before going to next step.

For testing your code, simply run:

```bash
uv run pytest
```

## Building the documentation

The documentation is generated using Sphinx, based on the content
in `docs/source` and in the `manim_slides` Python package.

To generate the documentation, run the following:

```bash
cd docs
uv run make html
```

Then, the output index file is located at `docs/build/html/index.html` and
can be opened with any modern browser.

:::{warning}
Building the documentation can take quite some time, especially
the first time as it needs to render all the animations.

Further builds should run faster.
:::

## Proposing changes

Once you feel ready and think your contribution is ready to be reviewed,
create a [pull request](https://github.com/jeertmans/manim-slides/pulls)
and wait for a reviewer to check your work!

Many thanks to you!
