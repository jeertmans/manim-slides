import sys

import click

from .__version__ import __version__


@click.command()
def checkhealth() -> None:
    """Check Manim Slides' installation."""
    click.echo(f"Manim Slides version: {__version__}")
    click.echo(f"Python executable: {sys.executable}")
    click.echo("Manim bindings:")

    try:
        from manim import __version__ as manimce_version

        click.echo(f"\tmanim (version: {manimce_version})")
    except ImportError:
        click.secho("\tmanim not found", bold=True)

    try:
        # Manimlib parses sys.argv on import, so we clear it temporarily.
        old_argv = sys.argv
        sys.argv = [__file__]
        from manimlib import __version__ as manimlib_version

        sys.argv = old_argv

        click.echo(f"\tmanimgl (version: {manimlib_version})")
    except ImportError:
        click.secho("\tmanimgl not found", bold=True)

    try:
        from qtpy import API, QT_VERSION

        click.echo(f"Qt API: {API} (version: {QT_VERSION})")
    except ImportError:
        click.secho(
            "No Qt API found, some Manim Slides commands will not be available",
            bold=True,
        )
