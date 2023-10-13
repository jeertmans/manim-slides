from pathlib import Path
from typing import Any, List, Optional, Tuple

from manimlib import Scene, ThreeDCamera
from manimlib.utils.file_ops import get_sorted_integer_files

from .base import Base


class Slide(Base, Scene):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        Path("videos").mkdir(exist_ok=True)
        kwargs["file_writer_config"] = {
            "break_into_partial_movies": True,
            "output_directory": "",
            "write_to_movie": True,
        }

        kwargs.setdefault("preview", False)  # Avoid opening a preview window

        super().__init__(*args, **kwargs)

    @property
    def _frame_height(self) -> float:
        return self.frame_height  # type: ignore

    @property
    def _frame_width(self) -> float:
        return self.frame_width  # type: ignore

    @property
    def _background_color(self) -> str:
        """Returns the scene's background color."""
        return self.camera_config["background_color"].hex  # type: ignore

    @property
    def _resolution(self) -> Tuple[int, int]:
        """Returns the scene's resolution used during rendering."""
        return self.camera_config["pixel_width"], self.camera_config["pixel_height"]

    @property
    def _partial_movie_files(self) -> List[Path]:
        """Returns a list of partial movie files, a.k.a animations."""

        kwargs = {
            "remove_non_integer_files": True,
            "extension": self.file_writer.movie_file_extension,
        }
        return [
            Path(file)
            for file in get_sorted_integer_files(
                self.file_writer.partial_movie_directory, **kwargs
            )
        ]

    @property
    def _show_progress_bar(self) -> bool:
        return getattr(self, "show_progress_bar", True)

    @property
    def _leave_progress_bar(self) -> bool:
        return getattr(self, "leave_progress_bars", False)

    @property
    def _start_at_animation_number(self) -> Optional[int]:
        return getattr(self, "start_at_animation_number", None)


class ThreeDSlide(Slide):
        CONFIG = {
            "camera_class": ThreeDCamera,
        }
        pass
