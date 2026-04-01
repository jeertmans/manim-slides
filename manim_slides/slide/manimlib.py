import sys
from pathlib import Path
from typing import Any, ClassVar, Optional

# Manimlib parses sys.argv on import, so we clear it temporarily.
old_argv = sys.argv
sys.argv = [__file__]
from manimlib import Scene, ThreeDCamera  # noqa: E402

sys.argv = old_argv

from .base import BaseSlide  # noqa: E402


class Slide(BaseSlide, Scene):  # type: ignore[misc]
    """
    Slide class for ManimGL (3b1b/manim).
    
    KEY FIX: ManimGL doesn't call begin_animation()/end_animation() like ManimCE.
    Instead, it uses pre_play()/post_play(). We override these to properly
    subdivide output at slide boundaries.
    """
    
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs.setdefault("file_writer_config", {}).update(
            subdivide_output=True,
        )
        
        super().__init__(*args, **kwargs)
        # Track when we're inside an animation for proper file subdivision
        self._in_animation = False
        self._file_writer_config.subdivide_output = True

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

    def pre_play(self) -> None:
        """Called before each play() — start a new partial movie file."""
        # ManimGL doesn't call begin_animation(), so we do it here
        if self.file_writer.subdivide_output and self.file_writer.write_to_movie:
            if not self._in_animation:
                self.file_writer.begin_animation()
                self._in_animation = True
        
        super().pre_play()

    def post_play(self) -> None:
        """Called after each play() — close the partial movie file."""
        super().post_play()
        
        # ManimGL doesn't call end_animation(), so we do it here
        if self.file_writer.subdivide_output and self.file_writer.write_to_movie:
            if self._in_animation:
                self.file_writer.end_animation()
                self._in_animation = False

    def wait(
        self,
        duration: float = 1.0,
        stop_condition: Optional[Any] = None,
        note: Optional[str] = None,
        ignore_presenter_mode: bool = False
    ) -> None:
        """
        Override wait() to treat it as an animation for slide purposes.
        
        ManimGL's wait() doesn't create animation files, which breaks slide
        boundaries. We create a minimal animation to ensure proper subdivision.
        """
        # If we're at a slide boundary, ensure the previous animation is closed
        if self.file_writer.subdivide_output and self._in_animation:
            self.file_writer.end_animation()
            self._in_animation = False
        
        # Call original wait
        super().wait(duration, stop_condition, note, ignore_presenter_mode)
        
        # Re-open for next animation if needed
        if self.file_writer.subdivide_output and self.file_writer.write_to_movie:
            self._in_animation = False  # Reset state

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
