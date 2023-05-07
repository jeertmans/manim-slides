# Workflow

This document is there to help you recreate a working environment for Manim Slides.

## Dependencies

```{include} ../../../README.md
:start-after: <!-- start deps -->
:end-before: <!-- end deps -->
```

## Forking the repository and cloning it locally

We used GitHub to host Manim Slides' repository, and we encourage contributors to use git.

Useful links:

* [GitHub's Hello World](https://docs.github.com/en/get-started/quickstart/hello-world).
* [GitHub Pull Request in 100 Seconds](https://www.youtube.com/watch?v=8lGpZkjnkt4&ab_channel=Fireship).

Once you feel comfortable with git and GitHub, [fork](https://github.com/jeertmans/manim-slides/fork) the repository, and clone it locally.

As for every Python project, using virtual environment is recommended to avoid conflicts between modules. For Manim Slides, we use [Poetry](https://python-poetry.org/docs/#installing-with-the-official-installer). If not already, please install it.

## Installing Python modules

With Poetry, installation becomes straightforward:

```bash
poetry install
```

This, however, only installs the minimal set of dependencies to run the package.

If you would like to install Manim or ManimGL, as documented in the [quickstart](../quickstart),
you can use the `--extras` option:

```bash
poetry install --extras manim   # For Manim
# or
poetry install --extras manimgl # For ManimGL
```

Additionnally, Manim Slides comes with group dependencies for development purposes:

```bash
poetry install --with dev  # For linters and formatters
# or
poetry install --with docs # To build the documentation locally
```

Another group is `test`, but it is only used for
[GitHub actions](https://github.com/jeertmans/manim-slides/blob/main/.github/workflows/test_examples.yml).

:::{note}
You can combine any number of groups or extras when installing the package locally.
:::

## Running commands

As modules were installed in a new Python environment, you cannot use them directly in the shell.
Instead, you either need to prepend `poetry run` to any command, e.g.:

```bash
poetry run manim-slides wizard
```

or enter a new shell that uses this new Python environment:

```
poetry shell
manim-slides wizard
```

## Testing your code

Most of the tests are done with GitHub actions, thus not on your computer. The only command you should run locally is `pre-commit run --all-files`: this runs a few linter and formatter to make sure the code quality and style stay constant across time. If a warning or an error is displayed, please fix it before going to next step.

## Proposing changes

Once you feel ready and think your contribution is ready to be reviewed, create a [pull request](https://github.com/jeertmans/manim-slides/pulls) and wait for a reviewer to check your work!

Many thanks to you!
