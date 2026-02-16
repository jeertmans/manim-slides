from datetime import datetime
from pathlib import Path
from typing import Optional

from qtpy.QtCore import Qt, QTimer, Signal, Slot
from qtpy.QtGui import QCloseEvent, QKeyEvent, QScreen
from qtpy.QtMultimedia import QAudioOutput, QMediaPlayer
from qtpy.QtMultimediaWidgets import QVideoWidget
from qtpy.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)

from ..config import Config, PresentationConfig
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

        self.scene_label = QLabel()
        self.slide_label = QLabel()
        self.start_time = datetime.now()
        self.time_label = QLabel()
        self.elapsed_label = QLabel("00h00m00s")
        self.timer = QTimer()
        self.timer.start(1000)
        self.timer.timeout.connect(self.update_time)

        bottom_left_layout = QHBoxLayout()
        for label, widget in [
            ("Scene:", self.scene_label),
            ("Slide:", self.slide_label),
            ("Time:", self.time_label),
            ("Elapsed:", self.elapsed_label),
        ]:
            bottom_left_layout.addWidget(QLabel(label))
            bottom_left_layout.addWidget(widget)

        left_layout.addLayout(bottom_left_layout)
        layout.addLayout(left_layout)
        layout.addSpacing(20)

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

        self.slide_notes = QLabel()
        self.slide_notes.setWordWrap(True)
        self.slide_notes.setTextFormat(Qt.TextFormat.MarkdownText)
        self.slide_notes.setFixedWidth(360)
        right_layout.addWidget(self.slide_notes)

        layout.addLayout(right_layout)

        widget = QWidget()
        widget.setLayout(layout)

        main_layout = QVBoxLayout()
        main_layout.addWidget(widget, alignment=Qt.AlignmentFlag.AlignCenter)
        self.setLayout(main_layout)

    @Slot()
    def update_time(self) -> None:
        now = datetime.now()
        seconds = int((now - self.start_time).total_seconds())
        h, rem = divmod(seconds, 3600)
        m, s = divmod(rem, 60)
        self.time_label.setText(now.strftime("%Y/%m/%d %H:%M:%S"))
        self.elapsed_label.setText(f"{h:02d}h{m:02d}m{s:02d}s")

    @Slot()
    def closeEvent(self, event: QCloseEvent) -> None:
        self.close_event.emit(event)

    @Slot()
    def keyPressEvent(self, event: QKeyEvent) -> None:
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

        self.config = config
        self.presentation_configs = presentation_configs
        self.__current_presentation_index = presentation_index
        self.__current_slide_index = slide_index
        self.__playing_reversed_slide = False
        self._loop_termination_scheduled = False

        self.__current_file: Path = self.current_slide_config.file

        self.media_player = QMediaPlayer(self)
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)

        self.video_widget = QVideoWidget()
        self.video_widget.setAspectRatioMode(aspect_ratio_mode)
        self.setCentralWidget(self.video_widget)
        self.media_player.setVideoOutput(self.video_widget)

        self.next_terminates_loop = next_terminates_loop
        self.exit_after_last_slide = exit_after_last_slide

        if self.current_slide_config.loop:
            self.media_player.setLoops(-1)

        self.load_current_media(start_paused=start_paused)

    @Slot()
    def next(self) -> None:
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PausedState:
            self.media_player.play()
            return

        if self.next_terminates_loop and self.media_player.loops() != 1:
            duration = self.media_player.duration()
            position = self.media_player.position()

            if duration <= 0:
                self.media_player.setLoops(1)
                return

            if self._loop_termination_scheduled:
                return

            remaining = max(0, duration - position)
            self._loop_termination_scheduled = True

            def finish_loop():
                self.media_player.setLoops(1)
                self._loop_termination_scheduled = False

            QTimer.singleShot(remaining, finish_loop)
            return

        self.load_next_slide()

    # ---- rest of methods unchanged ----
