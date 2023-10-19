from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional, Tuple

from manimlib import Scene, ThreeDCamera
from manimlib.utils.file_ops import get_sorted_integer_files

from .base import BaseSlide


class Slide(BaseSlide, Scene):  # type: ignore[misc]
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs.setdefault("file_writer_config", {}).update(
            skip_animations=True,
            break_into_partial_movies=True,
            write_to_movie=True,
        )

        kwargs["preview"] = False  # Avoid opening a preview window
        super().__init__(*args, **kwargs)

    @property
    def _frame_height(self) -> float:
        return self.camera.frame.get_height()  # type: ignore

    @property
    def _frame_width(self) -> float:
        return self.camera.frame.get_width()  # type: ignore

    @property
    def _background_color(self) -> str:
        return self.camera_config["background_color"].hex  # type: ignore

    @property
    def _resolution(self) -> Tuple[int, int]:
        return self.camera_config["pixel_width"], self.camera_config["pixel_height"]

    @property
    def _partial_movie_files(self) -> List[Path]:
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
        return True

    @property
    def _leave_progress_bar(self) -> bool:
        return self.leave_progress_bars  # type: ignore

    @property
    def _start_at_animation_number(self) -> Optional[int]:
        return self.start_at_animation_number  # type: ignore

    def run(self, *args: Any, **kwargs: Any) -> None:
        """MANIMGL renderer."""
        super().run(*args, **kwargs)
        self._save_slides(use_cache=False)


class ThreeDSlide(Slide):
    CONFIG: ClassVar[Dict[str, Any]] = {
        "camera_class": ThreeDCamera,
    }
    pass
