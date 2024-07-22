import sys

import click

from .__version__ import __version__


@click.command()
def checkhealth() -> None:
    """
    Check Manim Slides' installation.
    """
    click.echo(f"Manim Slides version: {__version__}")
    click.echo(f"Python executable: {sys.executable}")
