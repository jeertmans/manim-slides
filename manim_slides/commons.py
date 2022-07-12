import click

from .defaults import CONFIG_PATH


def config_path_option(function):
    return click.option(
        "-c",
        "--config",
        "config_path",
        default=CONFIG_PATH,
        type=click.Path(dir_okay=False),
        help="Set path to configuration file.",
    )(function)


def config_options(function):
    function = config_path_option(function)
    function = click.option(
        "-f", "--force", is_flag=True, help="Overwrite any existing configuration file."
    )(function)
    function = click.option(
        "-m",
        "--merge",
        is_flag=True,
        help="Merge any existing configuration file with the new configuration.",
    )(function)
    return function
