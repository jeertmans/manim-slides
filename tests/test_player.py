"""
Tests for the Qt player.

These tests focus on the ``--next-terminates-loop`` flag, and in particular
on the fact that terminating a looping slide must happen smoothly, i.e., at
the very end of the current loop iteration, without playing any frame of the
next iteration (see https://github.com/jeertmans/manim-slides/issues/500).
"""

from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from qtpy.QtCore import QEventLoop, QTimer
from qtpy.QtGui import QColor, QImage
from qtpy.QtMultimedia import QMediaPlayer, QVideoFrame
from qtpy.QtWidgets import QApplication

from manim_slides.config import Config, PresentationConfig
from manim_slides.present.player import LOOP_END_TOLERANCE_MS, Player

# Index of the looping slide in tests/data/slides/BasicSlide.json
LOOP_SLIDE_INDEX = 1


@pytest.fixture(scope="session")
def app() -> Iterator[QApplication]:
    """Yield a shared QApplication instance for the test session."""
    from manim_slides.qt_utils import qapp

    yield qapp()


@pytest.fixture
def player_factory(
    app: QApplication, slides_folder: Path
) -> Iterator[Callable[..., Player]]:
    """Yield a factory creating (and tracking) players on the looping slide."""
    players: list[Player] = []

    def factory(
        *,
        next_terminates_loop: bool = True,
        auto_next: bool = False,
    ) -> Player:
        """Create a player starting on the looping slide of BasicSlide.json."""
        presentation_config = PresentationConfig.from_file(
            slides_folder / "BasicSlide.json"
        )
        slides = [
            slide.model_copy(update={"auto_next": auto_next})
            if i == LOOP_SLIDE_INDEX
            else slide
            for i, slide in enumerate(presentation_config.slides)
        ]
        presentation_config = presentation_config.model_copy(update={"slides": slides})
        player = Player(
            Config(),
            [presentation_config],
            start_paused=False,
            next_terminates_loop=next_terminates_loop,
            hide_info_window=True,
            presentation_index=0,
            slide_index=LOOP_SLIDE_INDEX,
        )
        player.show([])
        players.append(player)
        return player

    yield factory

    for player in players:
        player.media_player.stop()
        player.close()


def process_events_for(ms: int) -> None:
    """Run the Qt event loop for the given amount of milliseconds."""
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


def wait_for_media_loaded(player: Player, timeout_ms: int = 5_000) -> int:
    """Wait until the media player knows the duration of the current media."""
    media_player = player.media_player
    elapsed = 0
    while media_player.duration() <= 0 and elapsed < timeout_ms:
        process_events_for(50)
        elapsed += 50

    duration = media_player.duration()
    assert duration > 0, "media duration was never reported"
    return duration


def make_video_frame(start_us: int, end_us: int) -> QVideoFrame:
    """Create a valid video frame with the given timestamps (in µs)."""
    image = QImage(8, 8, QImage.Format.Format_RGB32)
    image.fill(QColor("black"))
    frame = QVideoFrame(image)
    frame.setStartTime(start_us)
    frame.setEndTime(end_us)
    assert frame.isValid()
    return frame


def test_next_without_flag_advances_immediately(
    player_factory: Callable[..., Player],
) -> None:
    """
    Without the ``--next-terminates-loop`` flag, pressing next on a looping
    slide advances to the next slide immediately.
    """
    player = player_factory(next_terminates_loop=False)
    wait_for_media_loaded(player)
    process_events_for(200)

    player.next()

    assert player.current_slide_index == LOOP_SLIDE_INDEX + 1


def test_next_terminates_loop_at_end_of_iteration_auto_next(
    player_factory: Callable[..., Player],
) -> None:
    """
    Regression test for issue #500.

    When ``next`` is pressed during a looping slide with ``auto_next``, the
    next slide must be loaded as soon as the end of the current loop iteration
    is reached, i.e., before the position wraps around to 0. Terminating only
    after the wrap would play the first frame(s) of the next iteration, which
    is visible as a stutter.
    """
    player = player_factory(next_terminates_loop=True, auto_next=True)
    media_player = player.media_player
    duration = wait_for_media_loaded(player)
    assert media_player.loops() == -1

    process_events_for(300)
    player.next()  # request loop termination while playing

    assert player.current_slide_index == LOOP_SLIDE_INDEX
    assert player._Player__termination_requested

    # Freeze real position updates, then drive the position manually
    media_player.pause()
    position = media_player.position()

    # Any position within the current iteration must not terminate the loop
    media_player.positionChanged.emit(position)
    intermediate = min(position + 400, duration - 100)
    if intermediate > position:
        media_player.positionChanged.emit(intermediate)
    assert player.current_slide_index == LOOP_SLIDE_INDEX

    # Reaching the end of the iteration terminates the loop,
    # before the position wraps around to 0
    media_player.positionChanged.emit(duration)
    assert player.current_slide_index == LOOP_SLIDE_INDEX + 1


def test_next_terminates_loop_pauses_on_last_frame(
    player_factory: Callable[..., Player],
) -> None:
    """
    Without ``auto_next``, terminating a loop must pause the player on the
    last frame of the current iteration; pressing ``next`` again then loads
    the next slide.
    """
    player = player_factory(next_terminates_loop=True, auto_next=False)
    media_player = player.media_player
    duration = wait_for_media_loaded(player)

    process_events_for(300)
    player.next()  # request loop termination while playing

    media_player.pause()
    position = media_player.position()
    media_player.positionChanged.emit(position)
    assert player.current_slide_index == LOOP_SLIDE_INDEX
    assert not player._Player__termination_achieved

    # End of the current iteration: pause on the last frame, no slide change
    media_player.positionChanged.emit(duration)
    assert player.current_slide_index == LOOP_SLIDE_INDEX
    assert player._Player__termination_achieved
    assert media_player.playbackState() == QMediaPlayer.PlaybackState.PausedState

    # Pressing next again loads the next slide
    player.next()
    assert player.current_slide_index == LOOP_SLIDE_INDEX + 1


def test_next_terminates_loop_wrap_fallback(
    player_factory: Callable[..., Player],
) -> None:
    """
    If the end position is never reported by the backend, a non-monotonic
    position (loop wrap) must still trigger the termination.
    """
    player = player_factory(next_terminates_loop=True, auto_next=True)
    media_player = player.media_player
    wait_for_media_loaded(player)

    process_events_for(300)
    player.next()

    media_player.pause()
    position = media_player.position()
    media_player.positionChanged.emit(position)
    assert player.current_slide_index == LOOP_SLIDE_INDEX

    # Position wraps around to the beginning of the media
    media_player.positionChanged.emit(max(0, position - 500))
    assert player.current_slide_index == LOOP_SLIDE_INDEX + 1


def test_second_next_press_skips_terminating_loop(
    player_factory: Callable[..., Player],
) -> None:
    """
    Once loop termination has been requested, the looping slide behaves
    like a play slide: pressing ``next`` again skips to the next slide
    immediately.
    """
    player = player_factory(next_terminates_loop=True, auto_next=True)
    wait_for_media_loaded(player)

    process_events_for(300)
    player.next()
    assert player.current_slide_index == LOOP_SLIDE_INDEX

    player.next()
    assert player.current_slide_index == LOOP_SLIDE_INDEX + 1


def test_next_terminates_loop_auto_next_end_to_end(
    player_factory: Callable[..., Player],
) -> None:
    """
    With real playback, pressing next on a looping slide eventually
    advances to the next slide, at the end of the current iteration.
    """
    player = player_factory(next_terminates_loop=True, auto_next=True)
    media_player = player.media_player
    duration = wait_for_media_loaded(player)

    positions: list[tuple[int, int]] = []
    media_player.positionChanged.connect(
        lambda position: positions.append((position, player.current_slide_index))
    )

    process_events_for(300)
    player.next()

    for _ in range(100):
        process_events_for(50)
        if player.current_slide_index != LOOP_SLIDE_INDEX:
            break

    assert player.current_slide_index == LOOP_SLIDE_INDEX + 1

    loop_positions = [
        position for position, index in positions if index == LOOP_SLIDE_INDEX
    ]
    # The loop was left at the end of an iteration, never in the middle of
    # the next one (all positions stay within the media duration).
    assert loop_positions
    assert all(0 <= position <= duration for position in loop_positions)


def test_loop_wrap_frames_dropped_when_termination_pending(
    player_factory: Callable[..., Player],
) -> None:
    """
    Regression test for issue #500.

    Once loop termination is pending, frames from the next loop iteration
    (whose timestamps wrapped around to the beginning of the media) must be
    dropped, so that the animation ends smoothly on the last frame of the
    current iteration. Without a pending termination, wrapped frames are
    displayed normally (regular looping).
    """
    player = player_factory(next_terminates_loop=True)
    media_player = player.media_player
    wait_for_media_loaded(player)
    media_player.pause()

    last_frame = make_video_frame(1_933_000, 2_000_000)
    player.frame_changed(last_frame)
    assert player.frame.startTime() == 1_933_000

    # Termination pending: a wrapped frame (timestamp back near 0) is dropped
    player._Player__termination_requested = True
    wrapped_frame = make_video_frame(0, 66_000)
    player.frame_changed(wrapped_frame)
    assert player.frame.startTime() == 1_933_000

    # No termination pending: wrapped frames are displayed (normal looping)
    player._Player__termination_requested = False
    player.frame_changed(wrapped_frame)
    assert player.frame.startTime() == 0


def test_loop_end_tolerance_is_small() -> None:
    """
    The end-of-iteration detection tolerance must stay well below a
    single frame duration, so that termination never happens before the
    last frame of the iteration is displayed.
    """
    assert 0 < LOOP_END_TOLERANCE_MS <= 5
