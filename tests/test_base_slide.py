from collections.abc import MutableMapping

import pytest

from manim_slides.slide.base import BaseSlide


@pytest.fixture
def base_slide() -> BaseSlide:
    return BaseSlide()  # type: ignore[abstract]


class TestBaseSlide:
    def test_frame_height(self, base_slide: BaseSlide) -> None:
        with pytest.raises(NotImplementedError):
            _ = base_slide._frame_height

    def test_frame_width(self, base_slide: BaseSlide) -> None:
        with pytest.raises(NotImplementedError):
            _ = base_slide._frame_width

    def test_background_color(self, base_slide: BaseSlide) -> None:
        with pytest.raises(NotImplementedError):
            _ = base_slide._background_color

    def test_resolution(self, base_slide: BaseSlide) -> None:
        with pytest.raises(NotImplementedError):
            _ = base_slide._resolution

    def test_partial_movie_files(self, base_slide: BaseSlide) -> None:
        with pytest.raises(NotImplementedError):
            _ = base_slide._partial_movie_files

    def test_show_progress_bar(self, base_slide: BaseSlide) -> None:
        with pytest.raises(NotImplementedError):
            _ = base_slide._show_progress_bar

    def test_leave_progress_bar(self, base_slide: BaseSlide) -> None:
        with pytest.raises(NotImplementedError):
            _ = base_slide._leave_progress_bar

    def test_start_at_animation_number(self, base_slide: BaseSlide) -> None:
        with pytest.raises(NotImplementedError):
            _ = base_slide._start_at_animation_number

    def test_canvas(self, base_slide: BaseSlide) -> None:
        assert len(base_slide.canvas) == 0
        assert isinstance(base_slide.canvas, MutableMapping)

    def test_add_to__and_remove_from_canvas(self, base_slide: BaseSlide) -> None:
        assert len(base_slide.canvas) == 0

        base_slide.add_to_canvas(a=1, b=2)

        assert len(base_slide.canvas) == 2
        assert base_slide.canvas["a"] == 1
        assert base_slide.canvas["b"] == 2

        with pytest.raises(KeyError):
            _ = base_slide.canvas["c"]

        base_slide.add_to_canvas(b=3, c=4)

        assert len(base_slide.canvas) == 3

        assert sorted(base_slide.canvas_mobjects) == [1, 3, 4]

        base_slide.remove_from_canvas("a", "b", "c")

        assert len(base_slide.canvas) == 0

        with pytest.raises(KeyError):
            base_slide.remove_from_canvas("a")

    def test_mobjects_without_canvas(self) -> None:
        pass  # This property should be tested in test_slide.py

    def test_wait_time_between_slides(self, base_slide: BaseSlide) -> None:
        assert base_slide.wait_time_between_slides == 0.0

        base_slide.wait_time_between_slides = 1.0

        assert base_slide.wait_time_between_slides == 1.0

        base_slide.wait_time_between_slides = -1.0

        assert base_slide.wait_time_between_slides == 0.0

    def test_play(self) -> None:
        pass  # This method should be tested in test_slide.py

    def test_next_slide(self) -> None:
        pass  # This method should be tested in test_slide.py

    def test_add_last_slide(self) -> None:
        pass  # This method should be tested in test_slide.py

    def test_save_slides(self) -> None:
        pass  # This method should be tested in test_slide.py

    def test_zoom(self) -> None:
        pass  # This method should be tested in test_slide.py

    def test_wipe(self) -> None:
        pass  # This method should be tested in test_slide.py
