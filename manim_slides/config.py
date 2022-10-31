import os
from enum import Enum
from typing import List, Optional, Set

from pydantic import BaseModel, root_validator, validator
from PySide6.QtCore import Qt

from .manim import logger


class Key(BaseModel):
    """Represents a list of key codes, with optionally a name."""

    ids: Set[int]
    name: Optional[str] = None

    def set_ids(self, *ids: int) -> None:
        self.ids = set(ids)

    @validator("ids", each_item=True)
    def id_is_posint(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Key ids cannot be negative integers")
        return v

    def match(self, key_id: int) -> bool:
        m = key_id in self.ids

        if m:
            logger.debug(f"Pressed key: {self.name}")

        return m


class Config(BaseModel):
    """General Manim Slides config"""

    QUIT: Key = Key(ids=[Qt.Key_Q], name="QUIT")
    CONTINUE: Key = Key(ids=[Qt.Key_Right], name="CONTINUE / NEXT")
    BACK: Key = Key(ids=[Qt.Key_Left], name="BACK")
    REVERSE: Key = Key(ids=[Qt.Key_V], name="REVERSE")
    REWIND: Key = Key(ids=[Qt.Key_R], name="REWIND")
    PLAY_PAUSE: Key = Key(ids=[Qt.Key_Space], name="PLAY / PAUSE")
    HIDE_MOUSE: Key = Key(ids=[Qt.Key_H], name="HIDE / SHOW MOUSE")

    @root_validator
    def ids_are_unique_across_keys(cls, values):
        ids = set()

        for key in values.values():
            if len(ids.intersection(key.ids)) != 0:
                raise ValueError(
                    "Two or more keys share a common key code: please make sure each key has distinct key codes"
                )
            ids.update(key.ids)

        return values

    def merge_with(self, other: "Config") -> "Config":
        for key_name, key in self:
            other_key = getattr(other, key_name)
            key.ids.update(other_key.ids)
            key.name = other_key.name or key.name

        return self


class SlideType(str, Enum):
    slide = "slide"
    loop = "loop"
    last = "last"


class SlideConfig(BaseModel):
    type: SlideType
    start_animation: int
    end_animation: int
    number: int
    terminated: bool = False

    @validator("start_animation", "end_animation")
    def index_is_posint(cls, v: int):
        if v < 0:
            raise ValueError("Animation index (start or end) cannot be negative")
        return v

    @validator("number")
    def number_is_strictly_posint(cls, v: int):
        if v <= 0:
            raise ValueError("Slide number cannot be negative or zero")
        return v

    @root_validator
    def start_animation_is_before_end(cls, values):
        if values["start_animation"] >= values["end_animation"]:

            if values["start_animation"] == values["end_animation"] == 0:
                raise ValueError(
                    "You have to play at least one animation (e.g., `self.wait()`) before pausing. If you want to start paused, use the approriate command-line option when presenting."
                )

            raise ValueError(
                "Start animation index must be strictly lower than end animation index"
            )

        return values

    def is_slide(self):
        return self.type == SlideType.slide

    def is_loop(self):
        return self.type == SlideType.loop

    def is_last(self):
        return self.type == SlideType.last


class PresentationConfig(BaseModel):
    slides: List[SlideConfig]
    files: List[str]

    @validator("files", pre=True, each_item=True)
    def is_file_and_exists(cls, v):
        if not os.path.exists(v):
            raise ValueError(
                f"Animation file {v} does not exist. Are you in the right directory?"
            )

        if not os.path.isfile(v):
            raise ValueError(f"Animation file {v} is not a file")

        return v

    @root_validator
    def animation_indices_match_files(cls, values):
        files = values.get("files")
        slides = values.get("slides")

        if files is None or slides is None:
            return values

        n_files = len(files)

        for slide in slides:
            if slide.end_animation > n_files:
                raise ValueError(
                    f"The following slide's contains animations not listed in files {files}: {slide}"
                )

        return values


DEFAULT_CONFIG = Config()
