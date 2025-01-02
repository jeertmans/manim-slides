from pathlib import Path
from typing import Any, ClassVar, Optional

from manimlib import Scene, ThreeDCamera

from .base import BaseSlide


class Slide(BaseSlide, Scene):  # type: ignore[misc]
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs.setdefault("file_writer_config", {}).update(
            subdivide_output=True,
        )

        super().__init__(*args, **kwargs)

    @property
    def _frame_height(self) -> float:
        return float(self.camera.get_frame_height())

    @property
    def _frame_width(self) -> float:
        return float(self.camera.get_frame_width())

    @property
    def _background_color(self) -> str:
        rgba = self.camera.background_rgba
        r = int(255 * rgba[0])
        g = int(255 * rgba[1])
        b = int(255 * rgba[2])
        if rgba[3] == 1.0:
            return f"#{r:02x}{g:02x}{b:02x}"

        a = int(255 * rgba[3])
        return f"#{r:02x}{g:02x}{b:02x}{a:02x}"

    @property
    def _resolution(self) -> tuple[int, int]:
        return self.camera.get_pixel_width(), self.camera.get_pixel_height()

    @property
    def _partial_movie_files(self) -> list[Path]:
        partial_movie_directory = self.file_writer.partial_movie_directory
        extension = self.file_writer.movie_file_extension
        return sorted(partial_movie_directory.glob(f"*{extension}"))

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
        self._save_slides(
            use_cache=False,
            flush_cache=self.flush_cache,
            skip_reversing=self.skip_reversing,
        )


class ThreeDSlide(Slide):
    CONFIG: ClassVar[dict[str, Any]] = {
        "camera_class": ThreeDCamera,
    }
    pass
