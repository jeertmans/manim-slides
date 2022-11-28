import os
import webbrowser
from enum import Enum
from typing import Any, Callable, Dict, Generator, List, Type

import click
import pkg_resources
from click import Context, Parameter
from pydantic import BaseModel

from .commons import folder_path_option, verbosity_option
from .config import PresentationConfig
from .present import get_scenes_presentation_config


def validate_config_option(
    ctx: Context, param: Parameter, value: Any
) -> Dict[str, str]:

    config = {}

    for c_option in value:
        try:
            key, value = c_option.split("=")
            config[key] = value
        except ValueError:
            raise click.BadParameter(
                f"Configuration options `{c_option}` could not be parsed into a proper (key, value) pair. Please use an `=` sign to separate key from value."
            )

    return config


class Converter(BaseModel):  # type: ignore
    presentation_configs: List[PresentationConfig] = []
    assets_dir: str = "{basename}_assets"

    def convert_to(self, dest: str) -> None:
        """Converts self, i.e., a list of presentations, into a given format."""
        raise NotImplementedError

    def open(self, file: str) -> bool:
        """Opens a file, generated with converter, using appropriate application."""
        return webbrowser.open(file)

    @classmethod
    def from_string(cls, s: str) -> Type["Converter"]:
        """Returns the appropriate converter from a string name."""
        return {
            "html": RevealJS,
        }[s]


class JSBool(str, Enum):
    true = "true"
    false = "false"


class RevealTheme(str, Enum):
    black = "black"
    white = "white"
    league = "league"
    beige = "beige"
    sky = "sky"
    night = "night"
    serif = "serif"
    simple = "simple"
    soralized = "solarized"
    blood = "blood"
    moon = "moon"


class RevealJS(Converter):
    background_color: str = "black"
    controls: JSBool = JSBool.false
    embedded: JSBool = JSBool.false
    fragments: JSBool = JSBool.false
    height: str = "100%"
    loop: JSBool = JSBool.false
    progress: JSBool = JSBool.false
    reveal_version: str = "3.7.0"
    reveal_theme: RevealTheme = RevealTheme.black
    shuffle: JSBool = JSBool.false
    title: str = "Manim Slides"
    width: str = "100%"

    class Config:
        use_enum_values = True

    def get_sections_iter(self) -> Generator[str, None, None]:
        """Generates a sequence of sections, one per slide, that will be included into the html template."""
        for presentation_config in self.presentation_configs:
            for slide_config in presentation_config.slides:
                file = presentation_config.files[slide_config.start_animation]
                file = os.path.join(self.assets_dir, os.path.basename(file))

                if slide_config.is_loop():
                    yield f'<section data-background-video="{file}" data-background-video-loop></section>'
                else:
                    yield f'<section data-background-video="{file}"></section>'

    def load_template(self) -> str:
        """Returns the RevealJS HTML template as a string."""
        return pkg_resources.resource_string(
            __name__, "data/revealjs_template.html"
        ).decode()

    def convert_to(self, dest: str) -> None:
        """Converts this configuration into a RevealJS HTML presentation, saved to DEST."""
        dirname = os.path.dirname(dest)
        basename, ext = os.path.splitext(os.path.basename(dest))

        self.assets_dir = self.assets_dir.format(
            dirname=dirname, basename=basename, ext=ext
        )
        full_assets_dir = os.path.join(dirname, self.assets_dir)

        os.makedirs(full_assets_dir, exist_ok=True)

        for presentation_config in self.presentation_configs:
            presentation_config.concat_animations().move_to(full_assets_dir)

        with open(dest, "w") as f:

            sections = "".join(self.get_sections_iter())

            revealjs_template = self.load_template()
            content = revealjs_template.format(sections=sections, **self.dict())

            f.write(content)


def show_config_options(function: Callable[..., Any]) -> Callable[..., Any]:
    """Wraps a function to add a `--show-config` option."""

    def callback(ctx: Context, param: Parameter, value: bool) -> None:

        if not value or ctx.resilient_parsing:
            return

        to = ctx.params.get("to")

        if to:
            converter = Converter.from_string(to)(scenes=[])
            for key, value in converter.dict().items():
                click.echo(f"{key}: {repr(value)}")

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
@click.argument("scenes", nargs=-1)
@folder_path_option
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
    callback=validate_config_option,
    help="Configuration options passed to the converter. E.g., pass `-cbackground_color=red` to set the background color to red (if supported).",
)
@show_config_options
@verbosity_option
def convert(
    scenes: List[str],
    folder: str,
    dest: str,
    to: str,
    open_result: bool,
    force: bool,
    config_options: Dict[str, str],
) -> None:
    """
    Convert SCENE(s) into a given format and writes the result in DEST.
    """

    presentation_configs = get_scenes_presentation_config(scenes, folder)

    converter = Converter.from_string(to)(
        presentation_configs=presentation_configs, **config_options
    )

    converter.convert_to(dest)

    if open_result:
        converter.open(dest)
