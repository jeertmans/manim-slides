from pathlib import Path
from typing import List

from PySide6.QtCore import QUrl
from PySide6.QtGui import QIcon, QKeyEvent
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import QMainWindow

from ..config import Config, PresentationConfig, SlideConfig
from ..logger import logger
from ..resources import *  # noqa: F401, F403

WINDOW_NAME = "Manim Slides"
WINDOW_INFO_NAME = f"{WINDOW_NAME}: Info"


class VideoPlayer(QMainWindow):
    def __init__(
        self,
        config: Config,
        presentation_configs: List[PresentationConfig],
        exit_after_last_slide: bool = False,
        start_paused: bool = False,
    ):
        super().__init__()

        # Wizard's config

        self.config = config

        # Presentation configs

        self.presentation_configs = presentation_configs
        self.__current_presentation_index = 0
        self.__current_slide_index = 0
        self.__current_file = self.current_slide_config.file

        self.__playing_reversed_slide = False

        # Widgets

        self.setWindowTitle(WINDOW_NAME)
        self.icon = QIcon(":/icon.png")
        self.setWindowIcon(self.icon)

        self.setGeometry(100, 100, 800, 600)

        self.video_widget = QVideoWidget()
        self.setCentralWidget(self.video_widget)

        self.media_player = QMediaPlayer(self)
        self.media_player.setVideoOutput(self.video_widget)

        self.load_current_media(start_paused=start_paused)

        # Misc

        self.exit_after_last_slide = exit_after_last_slide

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
            logger.warn(f"Could not set presentation index to {index}")

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
            logger.warn(f"Could not set slide index to {index}")

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

    def load_current_media(self, start_paused=False):
        url = QUrl.fromLocalFile(self.current_file)
        self.media_player.setSource(url)

        if start_paused:
            self.media_player.pause()
        else:
            self.media_player.play()

    def load_current_slide(self):
        slide_config = self.current_slide_config
        self.current_file = slide_config.file

        if slide_config.is_loop():
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
            self.closeAll()
        else:
            logger.info("No more slide to play.")
            return

        self.load_current_slide()

    def load_reversed_slide(self) -> None:
        self.playing_reversed_slide = True
        self.current_file = self.current_slide_config.rev_file
        self.load_current_media()

    def closeAll(self):
        self.deleteLater()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        key = event.key()
        if self.config.keys.HIDE_MOUSE.match(key):
            if self.hide_mouse:
                self.setCursor(Qt.ArrowCursor)
                self.hide_mouse = False
            else:
                self.setCursor(Qt.BlankCursor)
                self.hide_mouse = True

        elif self.config.keys.PLAY_PAUSE.match(key):
            state = self.media_player.playbackState()
            if state == QMediaPlayer.PausedState:
                self.media_player.play()
            elif state == QMediaPlayer.PlayingState:
                self.media_player.pause()

        elif self.config.keys.CONTINUE.match(key):
            if self.media_player.playbackState() == QMediaPlayer.PausedState:
                self.media_player.play()
            else:
                self.load_next_slide()

        elif self.config.keys.BACK.match(key):
            self.load_previous_slide()

        elif self.config.keys.REVERSE.match(key):
            self.load_reversed_slide()

        elif self.config.keys.QUIT.match(key):
            self.closeAll()
        event.accept()
