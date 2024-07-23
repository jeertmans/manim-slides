"""Manim Slides' CLI."""

import json

import click
import requests
from click_default_group import DefaultGroup

from ..__version__ import __version__
from ..core.logger import logger
from .convert.commands import convert
from .present.commands import list_scenes, present
from .render.commands import render
from .wizard.commands import init, wizard


@click.group(cls=DefaultGroup, default="present", default_if_no_args=True)
@click.option(
    "--notify-outdated-version/--silent",
    " /-S",
    is_flag=True,
    default=True,
    help="Check if a new version of Manim Slides is available.",
)
@click.version_option(__version__, "-v", "--version")
@click.help_option("-h", "--help")
def main(notify_outdated_version: bool) -> None:
    """
    Manim Slides command-line utilities.

    If no command is specified, defaults to `present`.
    """
    # Code below is mostly a copy from:
    # https://github.com/ManimCommunity/manim/blob/main/manim/cli/render/commands.py
    if notify_outdated_version:
        manim_info_url = "https://pypi.org/pypi/manim-slides/json"
        warn_prompt = "Cannot check if latest release of Manim Slides is installed"
        try:
            req_info: requests.models.Response = requests.get(manim_info_url, timeout=2)
            req_info.raise_for_status()
            stable = req_info.json()["info"]["version"]
            if stable != __version__:
                click.echo(
                    "You are using Manim Slides version "
                    + click.style(f"v{__version__}", fg="red")
                    + ", but version "
                    + click.style(f"v{stable}", fg="green")
                    + " is available."
                )
                click.echo(
                    "You should consider upgrading via "
                    + click.style("pip install -U manim-slides", fg="yellow")
                )
        except requests.exceptions.HTTPError:
            logger.debug(f"HTTP Error: {warn_prompt}")
        except requests.exceptions.ConnectionError:
            logger.debug(f"Connection Error: {warn_prompt}")
        except requests.exceptions.Timeout:
            logger.debug(f"Timed Out: {warn_prompt}")
        except json.JSONDecodeError:
            logger.debug(warn_prompt)
            logger.debug(f"Error decoding JSON from {manim_info_url}")
        except Exception:
            logger.debug(f"Something went wrong: {warn_prompt}")


main.add_command(convert)
main.add_command(init)
main.add_command(list_scenes)
main.add_command(present)
main.add_command(render)
main.add_command(wizard)
