import json
import shutil
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import rtoml
from pydantic import (
    BaseModel,
    Field,
    FilePath,
    PositiveInt,
    field_validator,
    model_validator,
)
from pydantic_extra_types.color import Color
from PySide6.QtCore import Qt

from .logger import logger


class Key(BaseModel):  # type: ignore
    """Represents a list of key codes, with optionally a name."""

    ids: List[PositiveInt] = Field(unique=True)
    name: Optional[str] = None

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


class Keys(BaseModel):  # type: ignore
    QUIT: Key = Key(ids=[Qt.Key_Q], name="QUIT")
    CONTINUE: Key = Key(ids=[Qt.Key_Right], name="CONTINUE / NEXT")
    BACK: Key = Key(ids=[Qt.Key_Left], name="BACK")
    REVERSE: Key = Key(ids=[Qt.Key_V], name="REVERSE")
    REWIND: Key = Key(ids=[Qt.Key_R], name="REWIND")
    PLAY_PAUSE: Key = Key(ids=[Qt.Key_Space], name="PLAY / PAUSE")
    HIDE_MOUSE: Key = Key(ids=[Qt.Key_H], name="HIDE / SHOW MOUSE")

    @model_validator(mode="before")
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


class Config(BaseModel):  # type: ignore
    """General Manim Slides config"""

    keys: Keys = Keys()

    @classmethod
    def from_file(cls, path: Path) -> "Config":
        """Reads a configuration from a file."""
        return cls.model_validate(rtoml.load(path))  # type: ignore

    def to_file(self, path: Path) -> None:
        """Dumps the configuration to a file."""
        rtoml.dump(self.model_dump(), path, pretty=True)

    def merge_with(self, other: "Config") -> "Config":
        self.keys = self.keys.merge_with(other.keys)
        return self


class SlideType(str, Enum):
    slide = "slide"
    loop = "loop"
    last = "last"


class PreSlideConfig(BaseModel):  # type: ignore
    type: SlideType
    start_animation: int
    end_animation: int

    @field_validator("start_animation", "end_animation")
    @classmethod
    def index_is_posint(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Animation index (start or end) cannot be negative")
        return v

    @model_validator(mode="before")
    def start_animation_is_before_end(
        cls, values: Dict[str, Union[SlideType, int, bool]]
    ) -> Dict[str, Union[SlideType, int, bool]]:
        if values["start_animation"] >= values["end_animation"]:  # type: ignore
            if values["start_animation"] == values["end_animation"] == 0:
                raise ValueError(
                    "You have to play at least one animation (e.g., `self.wait()`) before pausing. If you want to start paused, use the approriate command-line option when presenting. IMPORTANT: when using ManimGL, `self.wait()` is not considered to be an animation, so prefer to directly use `self.play(...)`."
                )

            raise ValueError(
                "Start animation index must be strictly lower than end animation index"
            )

        return values

    @property
    def slides_slice(self) -> slice:
        return slice(self.start_animation, self.end_animation)


class SlideConfig(BaseModel):  # type: ignore
    type: SlideType
    file: FilePath
    rev_file: FilePath
    terminated: bool = Field(False, exclude=True)

    @classmethod
    def from_pre_slide_config_and_files(
        cls, pre_slide_config: PreSlideConfig, file: Path, rev_file: Path
    ) -> "SlideConfig":
        return cls(type=pre_slide_config.type, file=file, rev_file=rev_file)

    def is_slide(self) -> bool:
        return self.type == SlideType.slide

    def is_loop(self) -> bool:
        return self.type == SlideType.loop

    def is_last(self) -> bool:
        return self.type == SlideType.last


class PresentationConfig(BaseModel):  # type: ignore
    slides: List[SlideConfig] = Field(min_length=1)
    resolution: Tuple[PositiveInt, PositiveInt] = (1920, 1080)
    background_color: Color = "black"

    @classmethod
    def from_file(cls, path: Path) -> "PresentationConfig":
        """Reads a presentation configuration from a file."""
        with open(path, "r") as f:
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
        """Dumps the presentation configuration to a file."""
        with open(path, "w") as f:
            f.write(self.model_dump_json(indent=2))

    def copy_to(self, folder: Path, use_cached: bool = True) -> "PresentationConfig":
        """
        Copy the files to a given directory.
        """
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
