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
    conset,
    field_serializer,
    field_validator,
    model_validator,
)
from pydantic_extra_types.color import Color

from .logger import logger

Receiver = Callable[..., Any]


class Signal(BaseModel):  # type: ignore[misc]
    __receivers: list[Receiver] = PrivateAttr(default_factory=list)

    def connect(self, receiver: Receiver) -> None:
        self.__receivers.append(receiver)

    def disconnect(self, receiver: Receiver) -> None:
        self.__receivers.remove(receiver)

    def emit(self, *args: Any) -> None:
        for receiver in self.__receivers:
            receiver(*args)


def key_id(name: str) -> PositiveInt:
    """Avoid importing Qt too early."""
    from qtpy.QtCore import Qt

    return getattr(Qt, f"Key_{name}")


class Key(BaseModel):  # type: ignore[misc]
    """Represents a list of key codes, with optionally a name."""

    ids: conset(PositiveInt, min_length=1)  # type: ignore[valid-type]
    name: Optional[str] = None

    __signal: Signal = PrivateAttr(default_factory=Signal)

    def set_ids(self, *ids: int) -> None:
        self.ids = set(ids)

    def match(self, key_id: int) -> bool:
        m = key_id in self.ids

        if m:
            logger.debug(f"Pressed key: {self.name}")

        return m

    @property
    def signal(self) -> Signal:
        return self.__signal

    def connect(self, function: Receiver) -> None:
        self.__signal.connect(function)

    @field_serializer("ids")
    def serialize_dt(self, ids: set[int]) -> list[int]:
        return list(self.ids)


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

    @classmethod
    def from_file(cls, path: Path) -> "Config":
        """Read a configuration from a file."""
        return cls.model_validate(rtoml.load(path))  # type: ignore

    def to_file(self, path: Path) -> None:
        """Dump the configuration to a file."""
        rtoml.dump(self.model_dump(), path, pretty=True)

    def merge_with(self, other: "Config") -> "Config":
        """Merge with another config."""
        self.keys = self.keys.merge_with(other.keys)
        return self


class BaseSlideConfig(BaseModel):  # type: ignore
    """Base class for slide config."""

    loop: bool = False
    auto_next: bool = False
    playback_rate: float = 1.0
    reversed_playback_rate: float = 1.0
    notes: str = ""
    dedent_notes: bool = True
    skip_animations: bool = False

    @classmethod
    def wrapper(cls, arg_name: str) -> Callable[..., Any]:
        """
        Wrap a function to transform keyword argument into an instance of this class.

        The function signature is updated to reflect the new keyword-only arguments.

        The wrapped function must follow two criteria:
        - its last parameter must be ``**kwargs`` (or equivalent);
        - and its second last parameter must be ``<arg_name>``.
        """

        def _wrapper_(fun: Callable[..., Any]) -> Callable[..., Any]:
            @wraps(fun)
            def __wrapper__(*args: Any, **kwargs: Any) -> Any:  # noqa: N807
                fun_kwargs = {
                    key: value
                    for key, value in kwargs.items()
                    if key not in cls.model_fields
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
                for field_name, field_info in cls.model_fields.items()
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
        if base_slide_config.dedent_notes:
            base_slide_config.notes = dedent(base_slide_config.notes)

        return base_slide_config


class PreSlideConfig(BaseSlideConfig):
    """Slide config to be used prior to rendering."""

    start_animation: int
    end_animation: int

    @classmethod
    def from_base_slide_config_and_animation_indices(
        cls,
        base_slide_config: BaseSlideConfig,
        start_animation: int,
        end_animation: int,
    ) -> "PreSlideConfig":
        return cls(
            start_animation=start_animation,
            end_animation=end_animation,
            **base_slide_config.model_dump(),
        )

    @field_validator("start_animation", "end_animation")
    @classmethod
    def index_is_posint(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Animation index (start or end) cannot be negative")
        return v

    @model_validator(mode="after")
    @classmethod
    def start_animation_is_before_end(
        cls, pre_slide_config: "PreSlideConfig"
    ) -> "PreSlideConfig":
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
    rev_file: FilePath

    @classmethod
    def from_pre_slide_config_and_files(
        cls, pre_slide_config: PreSlideConfig, file: Path, rev_file: Path
    ) -> "SlideConfig":
        return cls(file=file, rev_file=rev_file, **pre_slide_config.model_dump())


class PresentationConfig(BaseModel):  # type: ignore[misc]
    slides: list[SlideConfig] = Field(min_length=1)
    resolution: tuple[PositiveInt, PositiveInt] = (1920, 1080)
    background_color: Color = "black"

    @classmethod
    def from_file(cls, path: Path) -> "PresentationConfig":
        """Read a presentation configuration from a file."""
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
        """Dump the presentation configuration to a file."""
        with open(path, "w") as f:
            f.write(self.model_dump_json(indent=2))

    def copy_to(
        self,
        folder: Path,
        use_cached: bool = True,
        include_reversed: bool = True,
        prefix: str = "",
    ) -> None:
        """Copy the files to a given directory."""
        for slide_config in self.slides:
            file = slide_config.file
            rev_file = slide_config.rev_file

            dest = folder / f"{prefix}{file.name}"
            rev_dest = folder / f"{prefix}{rev_file.name}"

            if not use_cached or not dest.exists():
                shutil.copy(file, dest)

            if include_reversed and (not use_cached or not rev_dest.exists()):
                shutil.copy(rev_file, rev_dest)
