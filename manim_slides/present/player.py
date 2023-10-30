from pathlib import Path
from typing import Any, List, Optional

from PySide6.QtCore import Qt, QUrl, Signal, Slot
from PySide6.QtGui import QCloseEvent, QIcon, QKeyEvent, QScreen
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import QDialog, QGridLayout, QLabel, QMainWindow

from ..config import Config, PresentationConfig, SlideConfig
from ..logger import logger
from ..resources import *  # noqa: F403

WINDOW_NAME = "Manim Slides"


class Info(QDialog):  # type: ignore[misc]
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        layout = QGridLayout()
        self.scene_label = QLabel()
        self.slide_label = QLabel()

        layout.addWidget(QLabel("Scene:"), 1, 1)
        layout.addWidget(QLabel("Slide:"), 2, 1)
        layout.addWidget(self.scene_label, 1, 2)
        layout.addWidget(self.slide_label, 2, 2)
        self.setLayout(layout)
        self.setFixedWidth(150)
        self.setFixedHeight(80)

        if parent := self.parent():
            self.closeEvent = parent.closeEvent
            self.keyPressEvent = parent.keyPressEvent


class Player(QMainWindow):  # type: ignore[misc]
    presentation_changed: Signal = Signal()
    slide_changed: Signal = Signal()

    def __init__(
        self,
        config: Config,
        presentation_configs: List[PresentationConfig],
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

        self.video_widget = QVideoWidget()
        self.video_widget.setAspectRatioMode(aspect_ratio_mode)
        self.setCentralWidget(self.video_widget)

        self.media_player = QMediaPlayer(self)
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.setPlaybackRate(playback_rate)

        self.presentation_changed.connect(self.presentation_changed_callback)
        self.slide_changed.connect(self.slide_changed_callback)

        self.info = Info(parent=self)

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
                if status == QMediaPlayer.EndOfMedia:
                    self.load_next_slide()

            self.media_player.mediaStatusChanged.connect(media_status_changed)

        else:

            def media_status_changed(status: QMediaPlayer.MediaStatus) -> None:
                if (
                    status == QMediaPlayer.EndOfMedia
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
            logger.warn(f"Could not set presentation index to {index}.")
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
            logger.warn(f"Could not set slide index to {index}.")
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
    def playing_reversed_slide(self) -> bool:
        return self.__playing_reversed_slide

    @playing_reversed_slide.setter
    def playing_reversed_slide(self, playing_reversed_slide: bool) -> None:
        self.__playing_reversed_slide = playing_reversed_slide

    """
    Loading slides
    """

    def load_current_media(self, start_paused: bool = False) -> None:
        url = QUrl.fromLocalFile(self.current_file)
        self.media_player.setSource(url)

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
        self.info.scene_label.setText(f"{index+1:4d}/{count:4<d}")

    @Slot()
    def slide_changed_callback(self) -> None:
        index = self.current_slide_index
        count = self.current_slides_count
        self.info.slide_label.setText(f"{index+1:4d}/{count:4<d}")

    def show(self) -> None:
        super().show()
        self.info.show()

    @Slot()
    def close(self) -> None:
        logger.info("Closing gracefully...")
        super().close()

    @Slot()
    def next(self) -> None:
        if self.media_player.playbackState() == QMediaPlayer.PausedState:
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
        self.load_reversed_slide()

    @Slot()
    def replay(self) -> None:
        self.media_player.setPosition(0)
        self.media_player.play()

    @Slot()
    def play_pause(self) -> None:
        state = self.media_player.playbackState()
        if state == QMediaPlayer.PausedState:
            self.media_player.play()
        elif state == QMediaPlayer.PlayingState:
            self.media_player.pause()

    @Slot()
    def full_screen(self) -> None:
        if self.windowState() == Qt.WindowFullScreen:
            self.setWindowState(Qt.WindowNoState)
        else:
            self.setWindowState(Qt.WindowFullScreen)

    @Slot()
    def hide_mouse(self) -> None:
        if self.cursor().shape() == Qt.BlankCursor:
            self.setCursor(Qt.ArrowCursor)
        else:
            self.setCursor(Qt.BlankCursor)

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        self.close()

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        key = event.key()
        self.dispatch(key)
        event.accept()
