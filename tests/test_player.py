from pathlib import Path
from unittest.mock import MagicMock, patch

from qtpy.QtWidgets import QApplication

from manim_slides.config import Config, PresentationConfig, SlideConfig, SlideType
from manim_slides.present.player import Player


def test_player_backward_navigation() -> None:
    # Ensure QApplication is created
    _ = QApplication.instance() or QApplication([])

    config = MagicMock(spec=Config)
    config.keys = MagicMock()

    slide_cfg_1 = MagicMock(spec=SlideConfig)
    slide_cfg_1.file = Path("slide1.mp4")
    slide_cfg_1.type = SlideType.Video
    slide_cfg_1.loop = False
    slide_cfg_1.auto_next = False
    slide_cfg_1.playback_rate = 1.0
    slide_cfg_1.reversed_playback_rate = 1.0
    slide_cfg_1.notes = ""

    slide_cfg_2 = MagicMock(spec=SlideConfig)
    slide_cfg_2.file = Path("slide2.mp4")
    slide_cfg_2.type = SlideType.Video
    slide_cfg_2.loop = False
    slide_cfg_2.auto_next = False
    slide_cfg_2.playback_rate = 1.0
    slide_cfg_2.reversed_playback_rate = 1.0
    slide_cfg_2.notes = ""

    pres_cfg = MagicMock(spec=PresentationConfig)
    pres_cfg.slides = [slide_cfg_1, slide_cfg_2]
    pres_cfg.resolution = (1920, 1080)

    with (
        patch("manim_slides.present.player.QMediaPlayer"),
        patch("manim_slides.present.player.QAudioOutput"),
        patch("pathlib.Path.resolve", return_value=Path("resolved_path.mp4")),
    ):
        player = Player(
            config,
            [pres_cfg],
            presentation_index=0,
            slide_index=1,
            skip_all=True,
            hide_info_window=True,
        )

        assert player._navigated_backward is False  # nosec

        # Call load_previous_slide / previous
        player.previous()

        # Verify navigating backward set the flag
        assert player._navigated_backward is True  # nosec

        # Mock duration change to verify seeking and resetting flag
        player.media_player.duration = MagicMock(return_value=5000)
        player.duration_changed_callback(5000)

        # Verify seeking was triggered and flag is reset
        player.media_player.setPosition.assert_called_with(5000)
        player.media_player.pause.assert_called()
        assert player._navigated_backward is False  # nosec
