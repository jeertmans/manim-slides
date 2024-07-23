"""Manim Slides' configuration tools."""

import json
import shutil
from functools import wraps
from inspect import Parameter, signature
from pathlib import Path
from textwrap import dedent
from typing import Any, Callable, Optional

import rtoml
from pydantic import (
    BaseModel,
    Field,
    FilePath,
    PositiveInt,
    PrivateAttr,
    ValidationError,
    field_validator,
    model_validator,
)
from pydantic_extra_types.color import Color

from .logger import logger

Receiver = Callable[..., Any]


class Signal(BaseModel):  # type: ignore[misc]
    """Signal that notifies a list of receivers when it is emitted."""

    __receivers: set[Receiver] = PrivateAttr(default_factory=set)

    def connect(self, receiver: Receiver) -> None:
        """
        Connect a receiver to this signal.

        This is a no-op if the receiver was already connected to this signal.

        :param receiver: The receiver to connect.
        """
        self.__receivers.add(receiver)

    def disconnect(self, receiver: Receiver) -> None:
        """
        Disconnect a receiver from this signal.

        This is a no-op if the receiver was not connected to this signal.

        :param receiver: The receiver to disconnect.
        """
        self.__receivers.discard(receiver)

    def emit(self, *args: Any) -> None:
        """
        Emit this signal and call each of the attached receivers.

        :param args: Positional arguments passed to each receiver.
        """
        for receiver in self.__receivers:
            receiver(*args)


def key_id(name: str) -> PositiveInt:
    """
    Return the id corresponding to the given key name.

    :param str: The name of the key, e.g., 'Q'.
    :return: The corresponding id.
    """
    from qtpy.QtCore import Qt  # Avoid importing Qt too early."""

    return getattr(Qt, f"Key_{name}")


class Key(BaseModel):  # type: ignore[misc]
    """Represent a list of key codes, with optionally a name."""

    ids: list[PositiveInt] = Field(unique=True)
    name: Optional[str] = None

    __signal: Signal = PrivateAttr(default_factory=Signal)

    @field_validator("ids")
    @classmethod
    def ids_is_non_empty_set(cls, ids: set[Any]) -> set[Any]:
        if len(ids) <= 0:
            raise ValueError("Key's ids must be a non-empty set")
        return ids

    def set_ids(self, *ids: int) -> None:
        self.ids = list(set(ids))

    def match(self, key_id: int) -> bool:
        """
        Return whether a given key id matches this key.
        """
        m = key_id in self.ids

        if m:
            logger.debug(f"Pressed key: {self.name}")

        return m

    @property
    def signal(self) -> Signal:
        return self.__signal

    def connect(self, function: Receiver) -> None:
        self.__signal.connect(function)


class Keys(BaseModel):  # type: ignore[misc]
    QUIT: Key = Field(default_factory=lambda: Key(ids=[key_id("Q")], name="QUIT"))
    PLAY_PAUSE: Key = Field(
        default_factory=lambda: Key(ids=[key_id("Space")], name="PLAY / PAUSE")
    )
    NEXT: Key = Field(default_factory=lambda: Key(ids=[key_id("Right")], name="NEXT"))
    PREVIOUS: Key = Field(
        default_factory=lambda: Key(ids=[key_id("Left")], name="PREVIOUS")
    )
    REVERSE: Key = Field(default_factory=lambda: Key(ids=[key_id("V")], name="REVERSE"))
    REPLAY: Key = Field(default_factory=lambda: Key(ids=[key_id("R")], name="REPLAY"))
    FULL_SCREEN: Key = Field(
        default_factory=lambda: Key(ids=[key_id("F")], name="TOGGLE FULL SCREEN")
    )
    HIDE_MOUSE: Key = Field(
        default_factory=lambda: Key(ids=[key_id("H")], name="HIDE / SHOW MOUSE")
    )

    @model_validator(mode="before")
    @classmethod
    def ids_are_unique_across_keys(cls, values: dict[str, Key]) -> dict[str, Key]:
        ids: set[int] = set()

        for key in values.values():
            if len(ids.intersection(key["ids"])) != 0:
                raise ValueError(
                    "Two or more keys share a common key code: please make sure each key has distinct key codes"
                )
            ids.update(key["ids"])

        return values

    def merge_with(self, other: "Keys") -> "Keys":
        for key_name, key in self:
            other_key = getattr(other, key_name)
            key.ids = list(set(key.ids).union(other_key.ids))
            key.name = other_key.name or key.name

        return self

    def dispatch_key_function(self) -> Callable[[PositiveInt], None]:
        _dispatch = {}

        for _, key in self:
            for _id in key.ids:
                _dispatch[_id] = key.signal

        def dispatch(key: PositiveInt) -> None:
            if signal := _dispatch.get(key, None):
                signal.emit()

        return dispatch


class Config(BaseModel):  # type: ignore[misc]
    """General Manim Slides config."""

    keys: Keys = Field(default_factory=Keys)
    """The key mapping."""

    @classmethod
    def from_file(cls, path: Path) -> "Config":
        """Read a configuration from a file."""
        return cls.model_validate(rtoml.load(path))  # type: ignore

    def to_file(self, path: Path) -> None:
        """Dump this configuration to a file."""
        rtoml.dump(self.model_dump(), path, pretty=True)

    def merge_with(self, other: "Config") -> "Config":
        """
        Merge with another config.

        :param other: The other config to be merged with.
        :return: This config, updated.
        """
        self.keys = self.keys.merge_with(other.keys)
        return self


class BaseSlideConfig(BaseModel):  # type: ignore
    """Base class for slide config."""

    loop: bool = False
    """Whether this slide should loop."""
    auto_next: bool = False
    """Whether this slide is skipped upon completion."""
    playback_rate: float = 1.0
    """The speed at which the animation is played (1.0 is normal)."""
    reversed_playback_rate: float = 1.0
    """The speed at which the reversed animation is played."""
    notes: str = ""
    """The notes attached to this slide."""
    dedent_notes: bool = True
    """Whether to automatically remove any leading indentation in the notes."""

    @classmethod
    def wrapper(cls, arg_name: str) -> Callable[..., Any]:
        """
        Wrap a function to transform keyword argument into an instance of this class.

        The function signature is updated to reflect the new keyword-only arguments.

        The wrapped function must follow two criteria:
        - its last parameter must be ``**kwargs`` (or equivalent);
        - and its second last parameter must be ``<arg_name>``.

        :param arg_name: The name of the argument.
        :return: The wrapped function.
        """
        # TODO: improve docs and (maybe) type-hints too

        def _wrapper_(fun: Callable[..., Any]) -> Callable[..., Any]:
            @wraps(fun)
            def __wrapper__(*args: Any, **kwargs: Any) -> Any:  # noqa: N807
                fun_kwargs = {
                    key: value
                    for key, value in kwargs.items()
                    if key not in cls.__fields__
                }
                fun_kwargs[arg_name] = cls(**kwargs)
                return fun(*args, **fun_kwargs)

            sig = signature(fun)
            parameters = list(sig.parameters.values())
            parameters[-2:-1] = [
                Parameter(
                    field_name,
                    Parameter.KEYWORD_ONLY,
                    default=field_info.default,
                    annotation=field_info.annotation,
                )
                for field_name, field_info in cls.__fields__.items()
            ]

            sig = sig.replace(parameters=parameters)
            __wrapper__.__signature__ = sig  # type: ignore[attr-defined]

            return __wrapper__

        return _wrapper_

    @model_validator(mode="after")
    @classmethod
    def apply_dedent_notes(
        cls, base_slide_config: "BaseSlideConfig"
    ) -> "BaseSlideConfig":
        """
        Remove indentation from notes, if specified.

        :param base_slide_config: The current config.
        :return: The config, optionally modified.
        """
        if base_slide_config.dedent_notes:
            base_slide_config.notes = dedent(base_slide_config.notes)

        return base_slide_config


class PreSlideConfig(BaseSlideConfig):
    """Slide config to be used prior to rendering."""

    start_animation: int
    """The index of the first animation."""
    end_animation: int
    """The index after the last animation."""

    @classmethod
    def from_base_slide_config_and_animation_indices(
        cls,
        base_slide_config: BaseSlideConfig,
        start_animation: int,
        end_animation: int,
    ) -> "PreSlideConfig":
        """
        Create a config from a base config and animation indices.

        :param base_slide_config: The base config.
        :param start_animation: The index of the first animation.
        :param end_animation: The index after the last animation.
        """
        return cls(
            start_animation=start_animation,
            end_animation=end_animation,
            **base_slide_config.dict(),
        )

    @field_validator("start_animation", "end_animation")
    @classmethod
    def index_is_posint(cls, v: int) -> int:
        """
        Validate that animation indices are positive integers.

        :param v: An animation index.
        :return: The animation index, if valid.
        """
        if v < 0:
            raise ValueError("Animation index (start or end) cannot be negative")
        return v

    @model_validator(mode="after")
    @classmethod
    def start_animation_is_before_end(
        cls, pre_slide_config: "PreSlideConfig"
    ) -> "PreSlideConfig":
        """
        Validate that start and end animation indices satisfy `start < end`.

        :param pre_slide_config: The current config.
        :return: The config, if indices are valid.
        """
        if pre_slide_config.start_animation >= pre_slide_config.end_animation:
            if pre_slide_config.start_animation == pre_slide_config.end_animation == 0:
                raise ValueError(
                    "You have to play at least one animation (e.g., `self.wait()`) "
                    "before pausing. If you want to start paused, use the appropriate "
                    "command-line option when presenting. "
                    "IMPORTANT: when using ManimGL, `self.wait()` is not considered "
                    "to be an animation, so prefer to directly use `self.play(...)`."
                )

            raise ValueError(
                "Start animation index must be strictly lower than end animation index"
            )

        return pre_slide_config

    @property
    def slides_slice(self) -> slice:
        return slice(self.start_animation, self.end_animation)


class SlideConfig(BaseSlideConfig):
    """Slide config to be used after rendering."""

    file: FilePath
    """The file containing the animation."""
    rev_file: FilePath
    """The file containing the reversed animation."""

    @classmethod
    def from_pre_slide_config_and_files(
        cls, pre_slide_config: PreSlideConfig, file: Path, rev_file: Path
    ) -> "SlideConfig":
        return cls(file=file, rev_file=rev_file, **pre_slide_config.dict())


class PresentationConfig(BaseModel):  # type: ignore[misc]
    """Presentation config that contains all necessary information for a presentation."""

    slides: list[SlideConfig] = Field(min_length=1)
    """The non-empty list of slide configs."""
    resolution: tuple[PositiveInt, PositiveInt] = (1920, 1080)
    """The resolution of the animation files."""
    background_color: Color = "black"
    """The background color of the animation files."""

    @classmethod
    def from_file(cls, path: Path) -> "PresentationConfig":
        """
        Read a presentation configuration from a file.

        :param path: The path where the config is read from.
        """
        with open(path) as f:
            obj = json.load(f)

            slides = obj.setdefault("slides", [])
            parent = path.parent.parent  # Never fails, but parents[1] can fail

            for slide in slides:
                if file := slide.get("file", None):
                    slide["file"] = parent / file

                if rev_file := slide.get("rev_file", None):
                    slide["rev_file"] = parent / rev_file

            return cls.model_validate(obj)  # type: ignore

    def to_file(self, path: Path) -> None:
        """
        Dump the presentation configuration to a file.

        :param path: The path to save this config.
        """
        with open(path, "w") as f:
            f.write(self.model_dump_json(indent=2))

    def copy_to(
        self,
        folder: Path,
        use_cached: bool = True,
        include_reversed: bool = True,
        prefix: str = "",
    ) -> "PresentationConfig":
        """
        Copy the files to a given directory and return the corresponding configuration.

        :param folder: The folder that will contain the animation files.
        :param use_cached: Whether caching should be used to avoid copies when possible.
        :param include_reversed: Whether to also copy reversed animation to the folder.
        :param prefix: Optional prefix added to each file name.
        """
        slides = []
        for slide_config in self.slides:
            file = slide_config.file
            rev_file = slide_config.rev_file

            dest = folder / f"{prefix}{file.name}"
            rev_dest = folder / f"{prefix}{rev_file.name}"

            slides.append(slide_config.model_copy(file=dest, rev_file=rev_dest))

            if not use_cached or not dest.exists():
                shutil.copy(file, dest)

            if include_reversed and (not use_cached or not rev_dest.exists()):
                # TODO: if include_reversed is False, then rev_dev will likely not exist
                # and this will cause an issue when decoding.
                shutil.copy(rev_file, rev_dest)

        return self.model_copy(slides=slides)


def list_presentation_configs(folder: Path) -> list[Path]:
    """
    List all presentation configs in a given folder.

    :param folder: The folder to search the presentation configs.
    :return: The list of paths that map to valid presentation configs.
    """
    paths = []

    for filepath in folder.glob("*.json"):
        try:
            _ = PresentationConfig.from_file(filepath)
            paths.append(filepath)
        except (
            ValidationError,
            json.JSONDecodeError,
        ) as e:  # Could not parse this file as a proper presentation config
            logger.warn(
                f"Something went wrong with parsing presentation config `{filepath}`: {e}."
            )

    logger.debug(
        f"Found {len(paths)} valid presentation configuration files in `{folder}`."
    )

    return paths
