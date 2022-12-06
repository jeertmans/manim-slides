import os
import webbrowser
from enum import Enum
from typing import Any, Callable, Dict, Generator, List, Type, Union

import click
import pkg_resources
from click import Context, Parameter
from pydantic import BaseModel, PositiveInt, ValidationError

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


class Str(str):
    """A simple string, but quoted when needed."""

    # This fixes pickling issue on Python 3.8
    __reduce_ex__ = str.__reduce_ex__

    def __str__(self) -> str:
        """Ensures that the string is correctly quoted."""
        if self in ["true", "false", "null"]:
            return super().__str__()
        else:
            return f"'{super().__str__()}'"


Function = str  # Basically, anything


class JsTrue(str, Enum):
    true = "true"


class JsFalse(str, Enum):
    false = "false"


class JsBool(Str, Enum):
    true = "true"
    false = "false"


class JsNull(Str, Enum):
    null = "null"


class ControlsLayout(Str, Enum):
    edges = "edges"
    bottom_right = "bottom-right"


class ControlsBackArrows(Str, Enum):
    faded = "faded"
    hidden = "hidden"
    visibly = "visibly"


class SlideNumber(Str, Enum):
    true = "true"
    false = "false"
    hdotv = "h.v"
    handv = "h/v"
    c = "c"
    candt = "c/t"


class ShowSlideNumber(Str, Enum):
    all = "all"
    print = "print"
    speaker = "speaker"


class KeyboardCondition(Str, Enum):
    null = "null"
    focused = "focused"


class NavigationMode(Str, Enum):
    default = "default"
    linear = "linear"
    grid = "grid"


class AutoPlayMedia(Str, Enum):
    null = "null"
    true = "true"
    false = "false"


PreloadIframes = AutoPlayMedia


class AutoAnimateMatcher(Str, Enum):
    null = "null"


class AutoAnimateEasing(Str, Enum):
    ease = "ease"


AutoSlide = Union[PositiveInt, JsFalse]


class AutoSlideMethod(Str, Enum):
    null = "null"


MouseWheel = Union[JsNull, float]


class Transition(Str, Enum):
    none = "none"
    fade = "fade"
    slide = "slide"
    convex = "convex"
    concave = "concave"
    zoom = "zoom"


class TransitionSpeed(Str, Enum):
    default = "default"
    fast = "fast"
    slow = "slow"


BackgroundTransition = Transition


class Display(Str, Enum):
    block = "block"


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
    # Presentation size options from RevealJS
    width: Union[Str, int] = Str("100%")
    height: Union[Str, int] = Str("100%")
    margin: float = 0.04
    min_scale: float = 0.2
    max_scale: float = 2.0
    # Configuration options from RevealJS
    controls: JsBool = JsBool.false
    controls_tutorial: JsBool = JsBool.true
    controls_layout: ControlsLayout = ControlsLayout.bottom_right
    controls_back_arrows: ControlsBackArrows = ControlsBackArrows.faded
    progress: JsBool = JsBool.false
    slide_number: SlideNumber = SlideNumber.false
    show_slide_number: Union[ShowSlideNumber, Function] = ShowSlideNumber.all
    hash_one_based_index: JsBool = JsBool.false
    hash: JsBool = JsBool.false
    respond_to_hash_changes: JsBool = JsBool.false
    history: JsBool = JsBool.false
    keyboard: JsBool = JsBool.true
    keyboard_condition: Union[KeyboardCondition, Function] = KeyboardCondition.null
    disable_layout: JsBool = JsBool.false
    overview: JsBool = JsBool.true
    center: JsBool = JsBool.true
    touch: JsBool = JsBool.true
    loop: JsBool = JsBool.false
    rtl: JsBool = JsBool.false
    navigation_mode: NavigationMode = NavigationMode.default
    shuffle: JsBool = JsBool.false
    fragments: JsBool = JsBool.true
    fragment_in_url: JsBool = JsBool.true
    embedded: JsBool = JsBool.false
    help: JsBool = JsBool.true
    pause: JsBool = JsBool.true
    show_notes: JsBool = JsBool.false
    auto_play_media: AutoPlayMedia = AutoPlayMedia.null
    preload_iframes: PreloadIframes = PreloadIframes.null
    auto_animate: JsBool = JsBool.true
    auto_animate_matcher: Union[AutoAnimateMatcher, Function] = AutoAnimateMatcher.null
    auto_animate_easing: AutoAnimateEasing = AutoAnimateEasing.ease
    auto_animate_duration: float = 1.0
    auto_animate_unmatched: JsBool = JsBool.true
    auto_animate_styles: List[str] = [
        "opacity",
        "color",
        "background-color",
        "padding",
        "font-size",
        "line-height",
        "letter-spacing",
        "border-width",
        "border-color",
        "border-radius",
        "outline",
        "outline-offset",
    ]
    auto_slide: AutoSlide = 0
    auto_slide_stoppable: JsBool = JsBool.true
    auto_slide_method: Union[AutoSlideMethod, Function] = AutoSlideMethod.null
    default_timing: Union[JsNull, int] = JsNull.null
    mouse_wheel: JsBool = JsBool.false
    preview_links: JsBool = JsBool.false
    post_message: JsBool = JsBool.true
    post_message_events: JsBool = JsBool.false
    focus_body_on_page_visibility_change: JsBool = JsBool.true
    transition: Transition = Transition.none
    transition_speed: TransitionSpeed = TransitionSpeed.default
    background_transition: BackgroundTransition = BackgroundTransition.none
    pdf_max_pages_per_slide: Union[int, str] = "Number.POSITIVE_INFINITY"
    pdf_separate_fragments: JsBool = JsBool.true
    pdf_page_height_offset: int = -1
    view_distance: int = 3
    mobile_view_distance: int = 2
    display: Display = Display.block
    hide_inactive_cursor: JsBool = JsBool.true
    hide_cursor_time: int = 5000
    # Add. options
    background_color: str = "black"  # TODO: use pydantic.color.Color
    reveal_version: str = "4.4.0"
    reveal_theme: RevealTheme = RevealTheme.black
    title: str = "Manim Slides"

    class Config:
        use_enum_values = True
        extra = "forbid"

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

    try:
        converter = Converter.from_string(to)(
            presentation_configs=presentation_configs, **config_options
        )

        converter.convert_to(dest)

        if open_result:
            converter.open(dest)

    except ValidationError as e:

        errors = e.errors()

        msg = [
            f"{len(errors)} error(s) occured with configuration options for '{to}', see below."
        ]

        for error in errors:
            option = error["loc"][0]
            _msg = error["msg"]
            msg.append(f"Option '{option}': {_msg}")

        raise click.UsageError("\n".join(msg))
