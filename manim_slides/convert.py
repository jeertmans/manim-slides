import mimetypes
import os
import platform
import shutil
import subprocess
import tempfile
import webbrowser
from base64 import b64encode
from collections import deque
from enum import Enum
from importlib import resources
from pathlib import Path
from typing import Any, Callable, Optional, Union

import av
import click
import pptx
from click import Context, Parameter
from jinja2 import Template
from lxml import etree
from PIL import Image
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    FilePath,
    GetCoreSchemaHandler,
    PositiveFloat,
    PositiveInt,
    ValidationError,
    conlist,
)
from pydantic_core import CoreSchema, core_schema
from pydantic_extra_types.color import Color
from tqdm import tqdm

from . import templates
from .commons import folder_path_option, verbosity_option
from .config import PresentationConfig
from .logger import logger
from .present import get_scenes_presentation_config


def open_with_default(file: Path) -> None:
    system = platform.system()
    if system == "Darwin":
        subprocess.call(("open", str(file)))
    elif system == "Windows":
        os.startfile(str(file))  # type: ignore[attr-defined]
    else:
        subprocess.call(("xdg-open", str(file)))


def validate_config_option(
    ctx: Context, param: Parameter, value: Any
) -> dict[str, str]:
    config = {}

    for c_option in value:
        try:
            key, value = c_option.split("=")
            config[key] = value
        except ValueError:
            raise click.BadParameter(
                f"Configuration options `{c_option}` could not be parsed into "
                "a proper (key, value) pair. "
                "Please use an `=` sign to separate key from value."
            ) from None

    return config


def file_to_data_uri(file: Path) -> str:
    """Read a video and return the corresponding data-uri."""
    b64 = b64encode(file.read_bytes()).decode("ascii")
    mime_type = mimetypes.guess_type(file)[0] or "video/mp4"

    return f"data:{mime_type};base64,{b64}"


def get_duration_ms(file: Path) -> float:
    """Read a video and return its duration in milliseconds."""
    with av.open(str(file)) as container:
        video = container.streams.video[0]

        return float(1000 * video.duration * video.time_base)


def read_image_from_video_file(file: Path, frame_index: "FrameIndex") -> Image:
    """Read a image from a video file at a given index."""
    with av.open(str(file)) as container:
        frames = container.decode(video=0)

        if frame_index == FrameIndex.last:
            (frame,) = deque(frames, 1)
        else:
            frame = next(frames)

        return frame.to_image()


class Converter(BaseModel):  # type: ignore
    presentation_configs: conlist(PresentationConfig, min_length=1)  # type: ignore[valid-type]
    assets_dir: str = "{basename}_assets"
    template: Optional[Path] = None

    def convert_to(self, dest: Path) -> None:
        """Convert self, i.e., a list of presentations, into a given format."""
        raise NotImplementedError

    def load_template(self) -> str:
        """
        Return the template as a string.

        An empty string is returned if no template is used.
        """
        return ""

    def open(self, file: Path) -> None:
        """Open a file, generated with converter, using appropriate application."""
        open_with_default(file)

    @classmethod
    def from_string(cls, s: str) -> type["Converter"]:
        """Return the appropriate converter from a string name."""
        return {
            "html": RevealJS,
            "pdf": PDF,
            "pptx": PowerPoint,
            "zip": HtmlZip,
        }[s]


class Str(str):
    """A simple string, but quoted when needed."""

    # This fixes pickling issue on Python 3.8
    __reduce_ex__ = str.__reduce_ex__

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return core_schema.str_schema()

    def __str__(self) -> str:
        """Ensure that the string is correctly quoted."""
        if self in ["true", "false", "null"]:
            return self
        else:
            return f"'{super().__str__()}'"


class StrEnum(Enum):
    def __str__(self) -> str:
        return str(self.value)


Function = str  # Basically, anything


class JsTrue(str, StrEnum):
    true = "true"


class JsFalse(str, StrEnum):
    false = "false"


class JsBool(Str, StrEnum):  # type: ignore
    true = "true"
    false = "false"


class JsNull(Str, StrEnum):  # type: ignore
    null = "null"


class ControlsLayout(Str, StrEnum):  # type: ignore
    edges = "edges"
    bottom_right = "bottom-right"


class ControlsBackArrows(Str, StrEnum):  # type: ignore
    faded = "faded"
    hidden = "hidden"
    visibly = "visibly"


class SlideNumber(Str, StrEnum):  # type: ignore
    true = "true"
    false = "false"
    hdotv = "h.v"
    handv = "h/v"
    c = "c"
    candt = "c/t"


class ShowSlideNumber(Str, StrEnum):  # type: ignore
    all = "all"
    print = "print"
    speaker = "speaker"


class KeyboardCondition(Str, StrEnum):  # type: ignore
    null = "null"
    focused = "focused"


class NavigationMode(Str, StrEnum):  # type: ignore
    default = "default"
    linear = "linear"
    grid = "grid"


class AutoPlayMedia(Str, StrEnum):  # type: ignore
    null = "null"
    true = "true"
    false = "false"


PreloadIframes = AutoPlayMedia


class AutoAnimateMatcher(Str, StrEnum):  # type: ignore
    null = "null"


class AutoAnimateEasing(Str, StrEnum):  # type: ignore
    ease = "ease"


AutoSlide = Union[PositiveInt, JsFalse]


class AutoSlideMethod(Str, StrEnum):  # type: ignore
    null = "null"


MouseWheel = Union[JsNull, float]


class Transition(Str, StrEnum):  # type: ignore
    none = "none"
    fade = "fade"
    slide = "slide"
    convex = "convex"
    concave = "concave"
    zoom = "zoom"


class TransitionSpeed(Str, StrEnum):  # type: ignore
    default = "default"
    fast = "fast"
    slow = "slow"


class BackgroundSize(Str, StrEnum):  # type: ignore
    # From: https://developer.mozilla.org/en-US/docs/Web/CSS/background-size
    # TODO: support more background size
    contain = "contain"
    cover = "cover"


BackgroundTransition = Transition


class Display(Str, StrEnum):  # type: ignore
    block = "block"


class RevealTheme(str, StrEnum):
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
    black_contrast = "black-contrast"
    white_contrast = "white-contrast"
    dracula = "dracula"


class RevealJS(Converter):
    # Export option: use data-uri
    data_uri: bool = False
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
    auto_animate_styles: list[str] = Field(
        default_factory=lambda: [
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
    )
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
    background_size: BackgroundSize = BackgroundSize.contain  # Not in RevealJS
    background_transition: BackgroundTransition = BackgroundTransition.none
    pdf_max_pages_per_slide: Union[int, str] = "Number.POSITIVE_INFINITY"
    pdf_separate_fragments: JsBool = JsBool.true
    pdf_page_height_offset: int = -1
    view_distance: int = 3
    mobile_view_distance: int = 2
    display: Display = Display.block
    hide_inactive_cursor: JsBool = JsBool.true
    hide_cursor_time: int = 5000
    # Appearance options from RevealJS
    background_color: Color = "black"
    reveal_version: str = "5.1.0"
    reveal_theme: RevealTheme = RevealTheme.black
    title: str = "Manim Slides"
    # Pydantic options
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    def load_template(self) -> str:
        """Return the RevealJS HTML template as a string."""
        if isinstance(self.template, Path):
            return self.template.read_text()

        return resources.files(templates).joinpath("revealjs.html").read_text()

    def open(self, file: Path) -> None:
        webbrowser.open(file.absolute().as_uri())

    def convert_to(self, dest: Path) -> None:
        """
        Convert this configuration into a RevealJS HTML presentation, saved to
        DEST.
        """
        if self.data_uri:
            assets_dir = Path("")  # Actually we won't care.
        else:
            dirname = dest.parent
            basename = dest.stem
            ext = dest.suffix

            assets_dir = Path(
                self.assets_dir.format(dirname=dirname, basename=basename, ext=ext)
            )
            full_assets_dir = dirname / assets_dir

            logger.debug(f"Assets will be saved to: {full_assets_dir}")

            full_assets_dir.mkdir(parents=True, exist_ok=True)

            num_presentation_configs = len(self.presentation_configs)

            if num_presentation_configs > 1:
                # Prevent possible name collision, see:
                # https://github.com/jeertmans/manim-slides/issues/428
                # With ManimCE, this can happen when caching is disabled as filenames are
                #   'uncached_000x.mp4'
                # With ManimGL, this can easily occur since filenames are just basic integers...
                num_digits = len(str(num_presentation_configs - 1))

                def prefix(i: int) -> str:
                    return f"s{i:0{num_digits}d}_"

            else:

                def prefix(i: int) -> str:
                    return ""

            for i, presentation_config in enumerate(self.presentation_configs):
                presentation_config.copy_to(
                    full_assets_dir, include_reversed=False, prefix=prefix(i)
                )

        dest.parent.mkdir(parents=True, exist_ok=True)

        with open(dest, "w") as f:
            revealjs_template = Template(self.load_template())

            options = self.model_dump()
            options["assets_dir"] = assets_dir

            has_notes = any(
                slide_config.notes != ""
                for presentation_config in self.presentation_configs
                for slide_config in presentation_config.slides
            )

            content = revealjs_template.render(
                file_to_data_uri=file_to_data_uri,
                get_duration_ms=get_duration_ms,
                has_notes=has_notes,
                env=os.environ,
                **options,
            )

            f.write(content)


class HtmlZip(RevealJS):
    def open(self, file: Path) -> None:
        super(RevealJS, self).open(file)  # Override opening with web browser

    def convert_to(self, dest: Path) -> None:
        """
        Convert this configuration into a zipped RevealJS HTML presentation, saved to
        DEST.
        """
        with tempfile.TemporaryDirectory() as directory_name:
            directory = Path(directory_name)

            html_file = directory / dest.with_suffix(".html").name

            super().convert_to(html_file)
            shutil.make_archive(str(dest.with_suffix("")), "zip", directory_name)


class FrameIndex(str, Enum):
    first = "first"
    last = "last"


class PDF(Converter):
    frame_index: FrameIndex = FrameIndex.last
    resolution: PositiveFloat = 100.0
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    def convert_to(self, dest: Path) -> None:
        """Convert this configuration into a PDF presentation, saved to DEST."""
        images = []

        for i, presentation_config in enumerate(self.presentation_configs):
            for slide_config in tqdm(
                presentation_config.slides,
                desc=f"Generating video slides for config {i + 1}",
                leave=False,
            ):
                images.append(
                    read_image_from_video_file(slide_config.file, self.frame_index)
                )

        dest.parent.mkdir(parents=True, exist_ok=True)

        images[0].save(
            dest,
            "PDF",
            resolution=self.resolution,
            save_all=True,
            append_images=images[1:],
        )


class PowerPoint(Converter):
    left: PositiveInt = 0
    top: PositiveInt = 0
    width: PositiveInt = 1280
    height: PositiveInt = 720
    auto_play_media: bool = True
    poster_frame_image: Optional[FilePath] = None
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    def convert_to(self, dest: Path) -> None:
        """Convert this configuration into a PowerPoint presentation, saved to DEST."""
        prs = pptx.Presentation()
        prs.slide_width = self.width * 9525
        prs.slide_height = self.height * 9525

        layout = prs.slide_layouts[6]  # Should be blank

        # From GitHub issue comment:
        # - https://github.com/scanny/python-pptx/issues/427#issuecomment-856724440
        def auto_play_media(
            media: pptx.shapes.picture.Movie, loop: bool = False
        ) -> None:
            el_id = xpath(media.element, ".//p:cNvPr")[0].attrib["id"]
            el_cnt = xpath(
                media.element.getparent().getparent().getparent(),
                f'.//p:timing//p:video//p:spTgt[@spid="{el_id}"]',
            )[0]
            cond = xpath(el_cnt.getparent().getparent(), ".//p:cond")[0]
            cond.set("delay", "0")

            if loop:
                ctn = xpath(el_cnt.getparent().getparent(), ".//p:cTn")[0]
                ctn.set("repeatCount", "indefinite")

        def xpath(el: etree.Element, query: str) -> etree.XPath:
            nsmap = {"p": "http://schemas.openxmlformats.org/presentationml/2006/main"}
            return etree.ElementBase.xpath(el, query, namespaces=nsmap)

        with tempfile.TemporaryDirectory() as directory_name:
            directory = Path(directory_name)
            frame_number = 0
            for i, presentation_config in enumerate(self.presentation_configs):
                for slide_config in tqdm(
                    presentation_config.slides,
                    desc=f"Generating video slides for config {i + 1}",
                    leave=False,
                ):
                    file = slide_config.file

                    mime_type = mimetypes.guess_type(file)[0]

                    if self.poster_frame_image is None:
                        poster_frame_image = str(directory / f"{frame_number}.png")
                        image = read_image_from_video_file(
                            file, frame_index=FrameIndex.first
                        )
                        image.save(poster_frame_image)

                        frame_number += 1
                    else:
                        poster_frame_image = str(self.poster_frame_image)

                    slide = prs.slides.add_slide(layout)
                    movie = slide.shapes.add_movie(
                        str(file),
                        self.left,
                        self.top,
                        self.width * 9525,
                        self.height * 9525,
                        poster_frame_image=poster_frame_image,
                        mime_type=mime_type,
                    )
                    if slide_config.notes != "":
                        slide.notes_slide.notes_text_frame.text = slide_config.notes

                    if self.auto_play_media:
                        auto_play_media(movie, loop=slide_config.loop)

            dest.parent.mkdir(parents=True, exist_ok=True)
            prs.save(dest)


def show_config_options(function: Callable[..., Any]) -> Callable[..., Any]:
    """Wrap a function to add a `--show-config` option."""

    def callback(ctx: Context, param: Parameter, value: bool) -> None:
        if not value or ctx.resilient_parsing:
            return

        to = ctx.params.get("to", "html")

        converter = Converter.from_string(to)

        for key, field in converter.model_fields.items():
            if field.is_required():
                continue

            default = field.get_default(call_default_factory=True)
            click.echo(f"{key}: {default}")

        ctx.exit()

    return click.option(  # type: ignore
        "--show-config",
        is_flag=True,
        help="Show supported options for given format and exit.",
        default=None,
        expose_value=False,
        show_envvar=True,
        callback=callback,
    )(function)


def show_template_option(function: Callable[..., Any]) -> Callable[..., Any]:
    """Wrap a function to add a `--show-template` option."""

    def callback(ctx: Context, param: Parameter, value: bool) -> None:
        if not value or ctx.resilient_parsing:
            return

        to = ctx.params.get("to", "html")
        template = ctx.params.get("template", None)

        converter = Converter.from_string(to)(
            presentation_configs=[PresentationConfig()], template=template
        )
        click.echo(converter.load_template())

        ctx.exit()

    return click.option(  # type: ignore
        "--show-template",
        is_flag=True,
        help="Show the template (currently) used for a given conversion format and exit.",
        default=None,
        expose_value=False,
        show_envvar=True,
        callback=callback,
    )(function)


@click.command()
@click.argument("scenes", nargs=-1)
@folder_path_option
@click.argument("dest", type=click.Path(dir_okay=False, path_type=Path))
@click.option(
    "--to",
    type=click.Choice(["auto", "html", "pdf", "pptx", "zip"], case_sensitive=False),
    metavar="FORMAT",
    default="auto",
    show_default=True,
    help="Set the conversion format to use. Use 'auto' to detect format from DEST.",
)
@click.option(
    "--open",
    "open_result",
    is_flag=True,
    help="Open the newly created file using the appropriate application.",
)
@click.option("-f", "--force", is_flag=True, help="Overwrite any existing file.")
@click.option(
    "-c",
    "--config",
    "config_options",
    multiple=True,
    callback=validate_config_option,
    help="Configuration options passed to the converter. "
    "E.g., pass ``-cslide_number=true`` to display slide numbers.",
)
@click.option(
    "--use-template",
    "template",
    metavar="FILE",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Use the template given by FILE instead of default one. "
    "To echo the default template, use ``--show-template``.",
)
@show_template_option
@show_config_options
@verbosity_option
def convert(
    scenes: list[str],
    folder: Path,
    dest: Path,
    to: str,
    open_result: bool,
    force: bool,
    config_options: dict[str, str],
    template: Optional[Path],
) -> None:
    """Convert SCENE(s) into a given format and writes the result in DEST."""
    presentation_configs = get_scenes_presentation_config(scenes, folder)

    try:
        if to == "auto":
            fmt = dest.suffix[1:].lower()
            try:
                cls = Converter.from_string(fmt)
            except KeyError:
                logger.warning(
                    f"Could not guess conversion format from {dest!s}, defaulting to HTML."
                )
                cls = RevealJS
        else:
            cls = Converter.from_string(to)

        converter = cls(
            presentation_configs=presentation_configs,
            template=template,
            **config_options,
        )

        converter.convert_to(dest)

        if open_result:
            converter.open(dest)

    except ValidationError as e:
        errors = e.errors()

        msg = [
            f"{len(errors)} error(s) occurred with configuration options for '{to}', see below."
        ]

        for error in errors:
            option = error["loc"][0]
            _msg = error["msg"]
            msg.append(f"Option '{option}': {_msg}")

        raise click.UsageError("\n".join(msg)) from None
