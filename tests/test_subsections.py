from __future__ import annotations

from pathlib import Path

import pytest

from manim_slides.config import BaseSlideConfig, PreSlideConfig, SubsectionMarker
from manim_slides.slide.base import BaseSlide


class DummySlide(BaseSlide):
    @property
    def _frame_height(self) -> float:
        return 1080.0

    @property
    def _frame_width(self) -> float:
        return 1920.0

    @property
    def _background_color(self) -> str:
        return "#000000"

    @property
    def _resolution(self) -> tuple[int, int]:
        return (1920, 1080)

    @property
    def _partial_movie_files(self) -> list[Path]:
        return []

    @property
    def _show_progress_bar(self) -> bool:
        return False

    @property
    def _leave_progress_bar(self) -> bool:
        return False

    @property
    def _start_at_animation_number(self) -> int | None:
        return None

    def play(self, *args: object, **kwargs: object) -> None:
        self._current_animation += 1


def test_build_subsection_configs(tmp_path: Path) -> None:
    slide = DummySlide(output_folder=tmp_path)
    base = BaseSlideConfig()
    pre_slide = PreSlideConfig.from_base_slide_config_and_animation_indices(
        base,
        start_animation=0,
        end_animation=3,
        subsection_markers=(
            SubsectionMarker(animation_index=1, name="Intro"),
            SubsectionMarker(animation_index=3, name="Wrap", auto_next=True),
        ),
    )

    durations = [0.2, 0.3, 0.5]
    # Create dummy animation files for validation
    partial_files = []
    for i in range(3):
        file_path = tmp_path / f"anim_{i}.mp4"
        file_path.touch()
        partial_files.append(file_path)

    subsections = slide._build_subsection_configs(pre_slide, durations, partial_files)

    assert len(subsections) == 2
    assert subsections[0].start_animation == 0
    assert subsections[0].end_animation == 1
    assert subsections[0].end_time == pytest.approx(0.2)
    assert subsections[1].start_animation == 1
    assert subsections[1].end_animation == 3
    assert subsections[1].end_time == pytest.approx(1.0)
    assert subsections[1].auto_next
    # Verify file field is populated correctly
    assert subsections[0].file == partial_files[0]  # Single animation: file set
    assert subsections[1].file is None  # Multiple animations: file is None


def test_build_subsection_configs_bounds(tmp_path: Path) -> None:
    slide = DummySlide(output_folder=tmp_path)
    base = BaseSlideConfig()
    pre_slide = PreSlideConfig.from_base_slide_config_and_animation_indices(
        base,
        start_animation=0,
        end_animation=2,
        subsection_markers=(SubsectionMarker(animation_index=5),),
    )

    # Create dummy animation files for validation
    partial_files = []
    for i in range(2):
        file_path = tmp_path / f"anim_{i}.mp4"
        file_path.touch()
        partial_files.append(file_path)

    with pytest.raises(ValueError):
        slide._build_subsection_configs(pre_slide, [0.1, 0.2], partial_files)
