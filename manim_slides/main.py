import click
from click_default_group import DefaultGroup

from . import __version__
from .present import list_scenes, present
from .wizard import init, wizard


@click.group(cls=DefaultGroup, default="present", default_if_no_args=True)
@click.version_option(__version__, "-v", "--version")
@click.help_option("-h", "--help")
def cli():
    pass


cli.add_command(list_scenes)
cli.add_command(present)
cli.add_command(wizard)
cli.add_command(init)

if __name__ == "__main__":
    cli()
