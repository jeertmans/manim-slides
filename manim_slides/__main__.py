import json

import click
import requests
from click_default_group import DefaultGroup

from .__version__ import __version__
from .checkhealth import checkhealth
from .config_lookup import load_merged_config, validate_defaults_against_command
from .convert import convert
from .logger import logger
from .present import list_scenes, present
from .render import render
from .wizard import init, wizard


def set_defaults_from_config(ctx: click.Context) -> None:
    """Populate ctx.default_map from the merged configuration files."""
    defaults = load_merged_config().defaults

    group = ctx.command
    assert isinstance(group, click.Group), "cli must be a click.Group"

    unknown_options = []

    for name, command in group.commands.items():
        command_defaults = defaults.root.get(name)

        if not command_defaults:
            continue

        unknown_options.extend(
            f"{name}.{key}"
            for key in validate_defaults_against_command(command, command_defaults)
        )

    if unknown_options:
        logger.warning(
            "Ignoring unknown configuration options: " + ", ".join(unknown_options)
        )

    ctx.default_map = defaults.root


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
def cli(notify_outdated_version: bool) -> None:
    """
    Manim Slides command-line utilities.

    If no command is specified, defaults to `present`.
    """
    set_defaults_from_config(click.get_current_context())

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
        except Exception:  # noqa: BLE001
            logger.debug(f"Something went wrong: {warn_prompt}")


cli.add_command(convert)
cli.add_command(checkhealth)
cli.add_command(init)
cli.add_command(list_scenes)
cli.add_command(present)
cli.add_command(render)
cli.add_command(wizard)

if __name__ == "__main__":
    cli()
