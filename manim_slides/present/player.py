from datetime import datetime
from pathlib import Path
from typing import Optional

from qtpy.QtCore import Qt, QTimer, QUrl, Signal, Slot
from qtpy.QtGui import QCloseEvent, QIcon, QKeyEvent, QScreen
from qtpy.QtMultimedia import QAudioOutput, QMediaPlayer, QVideoFrame
from qtpy.QtMultimediaWidgets import QVideoWidget
from qtpy.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)

from ..config import Config, PresentationConfig, SlideConfig
from ..logger import logger
from ..resources import *  # noqa: F403

WINDOW_NAME = "Manim Slides"


class Info(QWidget):  # type: ignore[misc]
    key_press_event: Signal = Signal(QKeyEvent)
    close_event: Signal = Signal(QCloseEvent)

    def __init__(
        self,
        *,
        aspect_ratio_mode: Qt.AspectRatioMode,
        screen: Optional[QScreen],
    ) -> None:
        super().__init__()

        if screen:
            self.setScreen(screen)
            self.move(screen.geometry().topLeft())

        layout = QHBoxLayout()

        # Current slide view

        left_layout = QVBoxLayout()
        left_layout.addWidget(
            QLabel("Current slide"),
            alignment=Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
        )
        main_video_widget = QVideoWidget()
        main_video_widget.setAspectRatioMode(aspect_ratio_mode)
        main_video_widget.setFixedSize(720, 480)
        self.video_sink = main_video_widget.videoSink()
        left_layout.addWidget(main_video_widget)

        # Current slide information

        self.scene_label = QLabel()
        self.slide_label = QLabel()
        self.start_time = datetime.now()
        self.time_label = QLabel()
        self.elapsed_label = QLabel("00h00m00s")
        self.timer = QTimer()
        self.timer.start(1000)  # every second
        self.timer.timeout.connect(self.update_time)

        bottom_left_layout = QHBoxLayout()
        bottom_left_layout.addWidget(
            QLabel("Scene:"),
            alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight,
        )
        bottom_left_layout.addWidget(
            self.scene_label,
            alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft,
        )
        bottom_left_layout.addWidget(
            QLabel("Slide:"),
            alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight,
        )
        bottom_left_layout.addWidget(
            self.slide_label,
            alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft,
        )
        bottom_left_layout.addWidget(
            QLabel("Time:"),
            alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight,
        )
        bottom_left_layout.addWidget(
            self.time_label,
            alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft,
        )
        bottom_left_layout.addWidget(
            QLabel("Elapsed:"),
            alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight,
        )
        bottom_left_layout.addWidget(
            self.elapsed_label,
            alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft,
        )
        left_layout.addLayout(bottom_left_layout)
        layout.addLayout(left_layout)

        layout.addSpacing(20)

        # Next slide preview

        right_layout = QVBoxLayout()
        right_layout.addWidget(
            QLabel("Next slide"),
            alignment=Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
        )
        next_video_widget = QVideoWidget()
        next_video_widget.setAspectRatioMode(aspect_ratio_mode)
        next_video_widget.setFixedSize(360, 240)
        self.next_media_player = QMediaPlayer()
        self.next_media_player.setVideoOutput(next_video_widget)
        self.next_media_player.setLoops(-1)

        right_layout.addWidget(next_video_widget)

        # Notes

        self.slide_notes = QLabel()
        self.slide_notes.setWordWrap(True)
        self.slide_notes.setTextFormat(Qt.TextFormat.MarkdownText)
        self.slide_notes.setFixedWidth(360)
        right_layout.addWidget(
            self.slide_notes,
            alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft,
        )
        layout.addLayout(right_layout)

        widget = QWidget()

        widget.setLayout(layout)

        main_layout = QVBoxLayout()
        main_layout.addWidget(widget, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setLayout(main_layout)

    @Slot()
    def update_time(self) -> None:
        now = datetime.now()
        seconds = (now - self.start_time).total_seconds()
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)
        self.time_label.setText(now.strftime("%Y/%m/%d %H:%M:%S"))
        self.elapsed_label.setText(
            f"{int(hours):02d}h{int(minutes):02d}m{int(seconds):02d}s"
        )

    @Slot()
    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        self.close_event.emit(event)

    @Slot()
    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        self.key_press_event.emit(event)


class Player(QMainWindow):  # type: ignore[misc]
    presentation_changed: Signal = Signal()
    slide_changed: Signal = Signal()

    def __init__(
        self,
        config: Config,
        presentation_configs: list[PresentationConfig],
        *,
        start_paused: bool = False,
        full_screen: bool = False,
        skip_all: bool = False,
        exit_after_last_slide: bool = False,
        hide_mouse: bool = False,
        aspect_ratio_mode: Qt.AspectRatioMode = Qt.KeepAspectRatio,
        presentation_index: int = 0,
        slide_index: int = 0,
        screen: Optional[QScreen] = None,
        playback_rate: float = 1.0,
        next_terminates_loop: bool = False,
        hide_info_window: bool = False,
        info_window_screen: Optional[QScreen] = None,
    ):
        super().__init__()

        # Wizard's config

        self.config = config

        # Presentation configs

        self.presentation_configs = presentation_configs
        self.__current_presentation_index = 0
        self.__current_slide_index = 0

        self.current_presentation_index = presentation_index
        self.current_slide_index = slide_index

        self.__current_file: Path = self.current_slide_config.file

        self.__playing_reversed_slide = False

        # Widgets

        if screen:
            self.setScreen(screen)
            self.move(screen.geometry().topLeft())

        if full_screen:
            self.setWindowState(Qt.WindowFullScreen)
        else:
            w, h = self.current_presentation_config.resolution
            geometry = self.geometry()
            geometry.setWidth(w)
            geometry.setHeight(h)
            self.setGeometry(geometry)

        if hide_mouse:
            self.setCursor(Qt.BlankCursor)

        self.setWindowTitle(WINDOW_NAME)
        self.icon = QIcon(":/icon.png")
        self.setWindowIcon(self.icon)

        self.frame = QVideoFrame()

        self.audio_output = QAudioOutput()
        self.video_widget = QVideoWidget()
        self.video_sink = self.video_widget.videoSink()
        self.video_widget.setAspectRatioMode(aspect_ratio_mode)
        self.setCentralWidget(self.video_widget)

        self.media_player = QMediaPlayer(self)
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)
        self.playback_rate = playback_rate

        self.presentation_changed.connect(self.presentation_changed_callback)
        self.slide_changed.connect(self.slide_changed_callback)

        self.info = Info(
            aspect_ratio_mode=aspect_ratio_mode,
            screen=info_window_screen,
        )
        self.info.close_event.connect(self.closeEvent)
        self.info.key_press_event.connect(self.keyPressEvent)
        self.video_sink.videoFrameChanged.connect(self.frame_changed)
        self.hide_info_window = hide_info_window

        # Connecting key callbacks

        self.config.keys.QUIT.connect(self.close)
        self.config.keys.PLAY_PAUSE.connect(self.play_pause)
        self.config.keys.NEXT.connect(self.next)
        self.config.keys.PREVIOUS.connect(self.previous)
        self.config.keys.REVERSE.connect(self.reverse)
        self.config.keys.REPLAY.connect(self.replay)
        self.config.keys.FULL_SCREEN.connect(self.full_screen)
        self.config.keys.HIDE_MOUSE.connect(self.hide_mouse)

        self.dispatch = self.config.keys.dispatch_key_function()

        # Misc

        self.exit_after_last_slide = exit_after_last_slide
        self.next_terminates_loop = next_terminates_loop

        # Setting-up everything

        if skip_all:

            def media_status_changed(status: QMediaPlayer.MediaStatus) -> None:
                self.media_player.setLoops(1)  # Otherwise looping slides never end
                if status == QMediaPlayer.MediaStatus.EndOfMedia:
                    self.load_next_slide()

            self.media_player.mediaStatusChanged.connect(media_status_changed)

        else:

            def media_status_changed(status: QMediaPlayer.MediaStatus) -> None:
                if (
                    status == QMediaPlayer.MediaStatus.EndOfMedia
                    and self.current_slide_config.auto_next
                ):
                    self.load_next_slide()

            self.media_player.mediaStatusChanged.connect(media_status_changed)

        if self.current_slide_config.loop:
            self.media_player.setLoops(-1)

        self.load_current_media(start_paused=start_paused)

        self.presentation_changed.emit()
        self.slide_changed.emit()

    """
    Properties
    """

    @property
    def presentations_count(self) -> int:
        return len(self.presentation_configs)

    @property
    def current_presentation_index(self) -> int:
        return self.__current_presentation_index

    @current_presentation_index.setter
    def current_presentation_index(self, index: int) -> None:
        if 0 <= index < self.presentations_count:
            self.__current_presentation_index = index
        elif -self.presentations_count <= index < 0:
            self.__current_presentation_index = index + self.presentations_count
        else:
            logger.warning(f"Could not set presentation index to {index}.")
            return

        self.presentation_changed.emit()

    @property
    def current_presentation_config(self) -> PresentationConfig:
        return self.presentation_configs[self.current_presentation_index]

    @property
    def current_slides_count(self) -> int:
        return len(self.current_presentation_config.slides)

    @property
    def current_slide_index(self) -> int:
        return self.__current_slide_index

    @current_slide_index.setter
    def current_slide_index(self, index: int) -> None:
        if 0 <= index < self.current_slides_count:
            self.__current_slide_index = index
        elif -self.current_slides_count <= index < 0:
            self.__current_slide_index = index + self.current_slides_count
        else:
            logger.warning(f"Could not set slide index to {index}.")
            return

        self.slide_changed.emit()

    @property
    def current_slide_config(self) -> SlideConfig:
        return self.current_presentation_config.slides[self.current_slide_index]

    @property
    def current_file(self) -> Path:
        return self.__current_file

    @current_file.setter
    def current_file(self, file: Path) -> None:
        self.__current_file = file

    @property
    def next_slide_config(self) -> Optional[SlideConfig]:
        if self.playing_reversed_slide:
            return self.current_slide_config
        elif self.current_slide_index < self.current_slides_count - 1:
            return self.presentation_configs[self.current_presentation_index].slides[
                self.current_slide_index + 1
            ]
        elif self.current_presentation_index < self.presentations_count - 1:
            return self.presentation_configs[
                self.current_presentation_index + 1
            ].slides[0]
        else:
            return None

    @property
    def next_file(self) -> Optional[Path]:
        if slide_config := self.next_slide_config:
            return slide_config.file  # type: ignore[no-any-return]

        return None

    @property
    def playing_reversed_slide(self) -> bool:
        return self.__playing_reversed_slide

    @playing_reversed_slide.setter
    def playing_reversed_slide(self, playing_reversed_slide: bool) -> None:
        self.__playing_reversed_slide = playing_reversed_slide

    """
    Loading slides
    """

    def load_current_media(self, start_paused: bool = False) -> None:
        url = QUrl.fromLocalFile(str(self.current_file))
        self.media_player.setSource(url)

        if self.playing_reversed_slide:
            self.media_player.setPlaybackRate(
                self.current_slide_config.reversed_playback_rate * self.playback_rate
            )
        else:
            self.media_player.setPlaybackRate(
                self.current_slide_config.playback_rate * self.playback_rate
            )

        if start_paused:
            self.media_player.pause()
        else:
            self.media_player.play()

    def load_current_slide(self) -> None:
        slide_config = self.current_slide_config
        self.current_file = slide_config.file

        if slide_config.loop:
            self.media_player.setLoops(-1)
        else:
            self.media_player.setLoops(1)

        self.load_current_media()

    def load_previous_slide(self) -> None:
        self.playing_reversed_slide = False

        if self.current_slide_index > 0:
            self.current_slide_index -= 1
        elif self.current_presentation_index > 0:
            self.current_presentation_index -= 1
            self.current_slide_index = self.current_slides_count - 1
        else:
            logger.info("No previous slide.")
            return

        self.load_current_slide()

    def load_next_slide(self) -> None:
        if self.playing_reversed_slide:
            self.playing_reversed_slide = False
            self.preview_next_slide()  # Slide number did not change, but next did
        elif self.current_slide_index < self.current_slides_count - 1:
            self.current_slide_index += 1
        elif self.current_presentation_index < self.presentations_count - 1:
            self.current_presentation_index += 1
            self.current_slide_index = 0
        elif self.exit_after_last_slide:
            self.close()
            return
        else:
            logger.info("No more slide to play.")
            return

        self.load_current_slide()

    def load_reversed_slide(self) -> None:
        self.playing_reversed_slide = True
        self.current_file = self.current_slide_config.rev_file
        self.load_current_media()

    """
    Key callbacks and slots
    """

    @Slot()
    def presentation_changed_callback(self) -> None:
        index = self.current_presentation_index
        count = self.presentations_count
        self.info.scene_label.setText(f"{index + 1:4d}/{count:4<d}")

    @Slot()
    def slide_changed_callback(self) -> None:
        index = self.current_slide_index
        count = self.current_slides_count
        self.info.slide_label.setText(f"{index + 1:4d}/{count:4<d}")
        self.info.slide_notes.setText(self.current_slide_config.notes)
        self.preview_next_slide()

    def preview_next_slide(self) -> None:
        if slide_config := self.next_slide_config:
            url = QUrl.fromLocalFile(str(slide_config.file))
            self.info.next_media_player.setSource(url)
            self.info.next_media_player.play()

    def show(self, screens: list[QScreen]) -> None:
        """Screens is necessary to prevent the info window from being shown on the same screen as the main window (especially in full screen mode)."""
        super().show()

        if not self.hide_info_window:
            if len(screens) > 1 and self.isFullScreen():
                self.ensure_different_screens(screens)

            if self.isFullScreen():
                self.info.showFullScreen()
            else:
                self.info.show()

            if (
                len(screens) > 1 and self.info.screen() == self.screen()
            ):  # It is better when Qt assigns the location, but if it fails to, this is a fallback
                self.ensure_different_screens(screens)

    def ensure_different_screens(self, screens: list[QScreen]) -> None:
        target_screen = screens[1] if self.screen() == screens[0] else screens[0]
        self.info.setScreen(target_screen)
        self.info.move(target_screen.geometry().topLeft())

    @Slot()
    def close(self) -> None:
        logger.info("Closing gracefully...")
        self.info.close()
        super().close()

    @Slot()
    def next(self) -> None:
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PausedState:
            self.media_player.play()
        elif self.next_terminates_loop and self.media_player.loops() != 1:
            position = self.media_player.position()
            self.media_player.setLoops(1)
            self.media_player.stop()
            self.media_player.setPosition(position)
            self.media_player.play()
        else:
            self.load_next_slide()

    @Slot()
    def previous(self) -> None:
        self.load_previous_slide()

    @Slot()
    def reverse(self) -> None:
        if self.playing_reversed_slide and self.current_slide_index >= 1:
            self.current_slide_index -= 1

        self.load_reversed_slide()
        self.preview_next_slide()

    @Slot()
    def replay(self) -> None:
        self.media_player.setPosition(0)
        self.media_player.play()

    @Slot()
    def play_pause(self) -> None:
        state = self.media_player.playbackState()
        if state == QMediaPlayer.PlaybackState.PausedState:
            self.media_player.play()
        elif state == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()

    @Slot()
    def full_screen(self) -> None:
        if self.windowState() == Qt.WindowFullScreen:
            self.setWindowState(Qt.WindowNoState)
            self.info.setWindowState(Qt.WindowNoState)
        else:
            self.setWindowState(Qt.WindowFullScreen)
            self.info.setWindowState(Qt.WindowFullScreen)

    @Slot()
    def hide_mouse(self) -> None:
        if self.cursor().shape() == Qt.BlankCursor:
            self.setCursor(Qt.ArrowCursor)
        else:
            self.setCursor(Qt.BlankCursor)

    def frame_changed(self, frame: QVideoFrame) -> None:
        """
        Slot to handle possibly invalid frames.

        This slot cannot be decorated with ``@Slot`` as
        the video sinks are handled in different threads.

        As of Qt>=6.5.3, the last frame of every video is "flushed",
        resulting in a short black screen between each slide.

        To avoid this issue, we check every frame, and avoid playing
        invalid ones.

        References
        ----------
        1. https://github.com/jeertmans/manim-slides/issues/293
        2. https://github.com/jeertmans/manim-slides/pull/464

        :param frame: The most recent frame.

        """
        if frame.isValid():
            self.frame = frame
        else:
            self.video_sink.setVideoFrame(self.frame)  # Reuse previous frame

        self.info.video_sink.setVideoFrame(self.frame)

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        self.close()

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        key = event.key()
        self.dispatch(key)
        event.accept()
