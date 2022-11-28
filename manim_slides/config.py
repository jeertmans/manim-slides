import os
import shutil
import subprocess
import tempfile
from enum import Enum
from typing import Callable, Dict, List, Optional, Set, Union

from pydantic import BaseModel, root_validator, validator
from PySide6.QtCore import Qt

from .manim import FFMPEG_BIN, logger


def merge_basenames(files: List[str]) -> str:
    """
    Merge multiple filenames by concatenating basenames.
    """

    dirname = os.path.dirname(files[0])
    _, ext = os.path.splitext(files[0])

    basename = "_".join(os.path.splitext(os.path.basename(file))[0] for file in files)

    return os.path.join(dirname, basename + ext)


class Key(BaseModel):  # type: ignore
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


class Config(BaseModel):  # type: ignore
    """General Manim Slides config"""

    QUIT: Key = Key(ids=[Qt.Key_Q], name="QUIT")
    CONTINUE: Key = Key(ids=[Qt.Key_Right], name="CONTINUE / NEXT")
    BACK: Key = Key(ids=[Qt.Key_Left], name="BACK")
    REVERSE: Key = Key(ids=[Qt.Key_V], name="REVERSE")
    REWIND: Key = Key(ids=[Qt.Key_R], name="REWIND")
    PLAY_PAUSE: Key = Key(ids=[Qt.Key_Space], name="PLAY / PAUSE")
    HIDE_MOUSE: Key = Key(ids=[Qt.Key_H], name="HIDE / SHOW MOUSE")

    @root_validator
    def ids_are_unique_across_keys(cls, values: Dict[str, Key]) -> Dict[str, Key]:
        ids: Set[int] = set()

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


class SlideConfig(BaseModel):  # type: ignore
    type: SlideType
    start_animation: int
    end_animation: int
    number: int
    terminated: bool = False

    @validator("start_animation", "end_animation")
    def index_is_posint(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Animation index (start or end) cannot be negative")
        return v

    @validator("number")
    def number_is_strictly_posint(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Slide number cannot be negative or zero")
        return v

    @root_validator
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

    def is_slide(self) -> bool:
        return self.type == SlideType.slide

    def is_loop(self) -> bool:
        return self.type == SlideType.loop

    def is_last(self) -> bool:
        return self.type == SlideType.last

    @property
    def slides_slice(self) -> slice:
        return slice(self.start_animation, self.end_animation)


class PresentationConfig(BaseModel):  # type: ignore
    slides: List[SlideConfig]
    files: List[str]

    @validator("files", pre=True, each_item=True)
    def is_file_and_exists(cls, v: str) -> str:
        if not os.path.exists(v):
            raise ValueError(
                f"Animation file {v} does not exist. Are you in the right directory?"
            )

        if not os.path.isfile(v):
            raise ValueError(f"Animation file {v} is not a file")

        return v

    @root_validator
    def animation_indices_match_files(
        cls, values: Dict[str, Union[List[SlideConfig], List[str]]]
    ) -> Dict[str, Union[List[SlideConfig], List[str]]]:
        files = values.get("files")
        slides = values.get("slides")

        if files is None or slides is None:
            return values

        n_files = len(files)

        for slide in slides:
            if slide.end_animation > n_files:  # type: ignore
                raise ValueError(
                    f"The following slide's contains animations not listed in files {files}: {slide}"
                )

        return values

    def move_to(self, dest: str, copy: bool = True) -> "PresentationConfig":
        """
        Moves (or copy) the files to a given directory.
        """
        copy_func: Callable[[str, str], None] = shutil.copy
        move_func: Callable[[str, str], None] = shutil.move
        move = copy_func if copy else move_func

        n = len(self.files)
        for i in range(n):
            file = self.files[i]
            basename = os.path.basename(file)
            dest_path = os.path.join(dest, basename)
            logger.debug(f"Moving / copying {file} to {dest_path}")
            move(file, dest_path)
            self.files[i] = dest_path

        return self

    def concat_animations(self, dest: Optional[str] = None) -> "PresentationConfig":
        """
        Concatenate animations such that each slide contains one animation.
        """

        dest_paths = []

        for i, slide_config in enumerate(self.slides):
            files = self.files[slide_config.slides_slice]

            if len(files) > 1:
                dest_path = merge_basenames(files)

                f = tempfile.NamedTemporaryFile(mode="w", delete=False)
                f.writelines(f"file {os.path.abspath(path)}\n" for path in files)
                f.close()

                command = [
                    FFMPEG_BIN,
                    "-f",
                    "concat",
                    "-safe",
                    "0",
                    "-i",
                    f.name,
                    "-c",
                    "copy",
                    dest_path,
                    "-y",
                ]
                logger.debug(" ".join(command))
                process = subprocess.Popen(
                    command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                output, error = process.communicate()

                if output:
                    logger.debug(output.decode())

                if error:
                    logger.debug(error.decode())

                dest_paths.append(dest_path)

            else:
                dest_paths.append(files[0])

            slide_config.start_animation = i
            slide_config.end_animation = i + 1

        self.files = dest_paths

        if dest:
            return self.move_to(dest)

        return self


DEFAULT_CONFIG = Config()
