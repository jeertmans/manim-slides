import click
from typing import Callable
from click import Context, Parameter

from .commons import verbosity_option


import webbrowser


class Converter:
    config = dict(a="test", b="hello")

    def __init__(self, scenes, **config):

        self.scenes = scenes
        self.config.update(**config)

    def convert(self, dest: str):
        raise NotImplementedError

    def open(self, file: str):
        raise NotImplementedError

    @classmethod
    def from_string(cls, s: str) -> "Converter":
        return {
            "html": RevealJS,
        }[s]


class RevealJS(Converter):
    def convert(self, dest):
        with open(dest, "w") as f:
            pass


def show_config_options(function: Callable) -> Callable:
    """Wraps a function to add a `--show-config` option."""

    def callback(ctx: Context, param: Parameter, value: bool) -> None:

        if not value or ctx.resilient_parsing:
            return

        to = ctx.params.get("to")

        if to:
            for key, value in Converter.from_string(to).config.items():
                click.echo(f"{key}: {value}")

            ctx.exit()

        else:
            raise click.UsageError(
                "Using --show-config option requires to first specify --to option."
            )

    return click.option(
        "--show-config",
        is_flag=True,
        help="Show supported options for given format and exit.",
        default=None,
        expose_value=False,
        show_envvar=True,
        callback=callback,
    )(function)


@click.command()
@click.pass_context
@click.argument("scenes", nargs=-1)
@click.argument("dest")
@click.option(
    "--to",
    type=click.Choice(["html"], case_sensitive=False),
    default="html",
    show_default=True,
    help="Set the conversion format to use.",
)
@click.option(
    "--open",
    "open_result",
    is_flag=True,
    help="Open the newly created file using the approriate application.",
)
@click.option("-f", "--force", is_flag=True, help="Overwrite any existing file.")
@click.option(
    "-c",
    "--config",
    "config_options",
    multiple=True,
    help="Configuration options passed to the converter.",
)
@show_config_options
@verbosity_option
def convert(ctx, scenes, dest, to, open_result, force, config_options):
    """
    Convert SCENE(s) into a given format and writes the result in DEST.
    """
    
    config = {}

    for c_option in config_options:
        try:
            key, value = c_option.split("=")
            config[key] = value
        except ValueError:
            raise click.UsageError(f"Configuration options `{c_option}` could not be parsed into a proper (key, value) pair. Please use an `=` sign to separate key from value.")
        

    print(config)

    print(scenes)
    print(dest)

    config = dict([item.strip("--").split("=") for item in ctx.args])
    print(config)

    converter = Converter.from_string(to)
