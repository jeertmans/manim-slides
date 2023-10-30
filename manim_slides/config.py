import json
import shutil
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import rtoml
from pydantic import (
    BaseModel,
    Field,
    FilePath,
    PositiveInt,
    PrivateAttr,
    field_validator,
    model_validator,
)
from pydantic_extra_types.color import Color
from PySide6.QtCore import Qt

from .logger import logger

Receiver = Callable[..., Any]


class Signal(BaseModel):  # type: ignore[misc]
    __receivers: List[Receiver] = PrivateAttr(default_factory=list)

    def connect(self, receiver: Receiver) -> None:
        self.__receivers.append(receiver)

    def disconnect(self, receiver: Receiver) -> None:
        self.__receivers.remove(receiver)

    def emit(self, *args: Any) -> None:
        for receiver in self.__receivers:
            receiver(*args)


class Key(BaseModel):  # type: ignore[misc]
    """Represents a list of key codes, with optionally a name."""

    ids: List[PositiveInt] = Field(unique=True)
    name: Optional[str] = None

    __signal: Signal = PrivateAttr(default_factory=Signal)

    @field_validator("ids")
    @classmethod
    def ids_is_non_empty_set(cls, ids: Set[Any]) -> Set[Any]:
        if len(ids) <= 0:
            raise ValueError("Key's ids must be a non-empty set")
        return ids

    def set_ids(self, *ids: int) -> None:
        self.ids = list(set(ids))

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


class Keys(BaseModel):  # type: ignore[misc]
    QUIT: Key = Key(ids=[Qt.Key_Q], name="QUIT")
    PLAY_PAUSE: Key = Key(ids=[Qt.Key_Space], name="PLAY / PAUSE")
    NEXT: Key = Key(ids=[Qt.Key_Right], name="NEXT")
    PREVIOUS: Key = Key(ids=[Qt.Key_Left], name="PREVIOUS")
    REVERSE: Key = Key(ids=[Qt.Key_V], name="REVERSE")
    REPLAY: Key = Key(ids=[Qt.Key_R], name="REPLAY")
    FULL_SCREEN: Key = Key(ids=[Qt.Key_F], name="TOGGLE FULL SCREEN")
    HIDE_MOUSE: Key = Key(ids=[Qt.Key_H], name="HIDE / SHOW MOUSE")

    @model_validator(mode="before")
    @classmethod
    def ids_are_unique_across_keys(cls, values: Dict[str, Key]) -> Dict[str, Key]:
        ids: Set[int] = set()

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

    keys: Keys = Keys()

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


class PreSlideConfig(BaseModel):  # type: ignore
    start_animation: int
    end_animation: int
    loop: bool = False
    auto_next: bool = False

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
                    "You have to play at least one animation (e.g., `self.wait()`) before pausing. If you want to start paused, use the approriate command-line option when presenting. IMPORTANT: when using ManimGL, `self.wait()` is not considered to be an animation, so prefer to directly use `self.play(...)`."
                )

            raise ValueError(
                "Start animation index must be strictly lower than end animation index"
            )

        return pre_slide_config

    @model_validator(mode="after")
    @classmethod
    def loop_and_auto_next_disallowed(
        cls, pre_slide_config: "PreSlideConfig"
    ) -> "PreSlideConfig":
        if pre_slide_config.loop and pre_slide_config.auto_next:
            raise ValueError(
                "You cannot have both `loop=True` and `auto_next=True`, "
                "because a looping slide has no ending. "
                "This may be supported in the future if "
                "https://github.com/jeertmans/manim-slides/pull/299 gets merged."
            )

        return pre_slide_config

    @property
    def slides_slice(self) -> slice:
        return slice(self.start_animation, self.end_animation)


class SlideConfig(BaseModel):  # type: ignore[misc]
    file: FilePath
    rev_file: FilePath
    loop: bool = False
    auto_next: bool = False

    @classmethod
    def from_pre_slide_config_and_files(
        cls, pre_slide_config: PreSlideConfig, file: Path, rev_file: Path
    ) -> "SlideConfig":
        return cls(
            file=file,
            rev_file=rev_file,
            loop=pre_slide_config.loop,
            auto_next=pre_slide_config.auto_next,
        )


class PresentationConfig(BaseModel):  # type: ignore[misc]
    slides: List[SlideConfig] = Field(min_length=1)
    resolution: Tuple[PositiveInt, PositiveInt] = (1920, 1080)
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

    def copy_to(self, folder: Path, use_cached: bool = True) -> "PresentationConfig":
        """Copy the files to a given directory."""
        for slide_config in self.slides:
            file = slide_config.file
            rev_file = slide_config.rev_file

            dest = folder / file.name
            rev_dest = folder / rev_file.name

            slide_config.file = dest
            slide_config.rev_file = rev_dest

            if not use_cached or not dest.exists():
                shutil.copy(file, dest)

            if not use_cached or not rev_dest.exists():
                shutil.copy(rev_file, rev_dest)

        return self


DEFAULT_CONFIG = Config()
