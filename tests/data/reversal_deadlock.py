"""
Force the inherited renderer-lock failure while reversing real video segments.

Run in a subprocess: this deliberately leaves fork workers blocked. The caller
must enforce a timeout and terminate the process group when testing old code.
"""

import logging
import multiprocessing
import os
import sys
from pathlib import Path
from threading import Event, Thread

import av
from manim import LEFT, RIGHT, Dot
from rich.logging import RichHandler

from manim_slides.logger import logger
from manim_slides.slide.manim import Slide
from manim_slides.utils import reverse_video_file


def install_inherited_renderer_lock() -> None:
    # Model Linux/Python <= 3.13 even when the host defaults to spawn/forkserver.
    multiprocessing.set_start_method("fork", force=True)
    handler = next(h for h in logger.handlers if isinstance(h, RichHandler))
    console = handler.console
    libav_logger = logging.getLogger("libav")
    libav_logger.handlers = [handler]
    libav_logger.setLevel(logging.INFO)
    libav_logger.propagate = False
    av.logging.set_level(av.logging.INFO)

    ready = Event()
    release = Event()
    threads: list[Thread] = []

    def hold_renderer_lock() -> None:
        with console._lock:
            ready.set()
            release.wait()

    def before_fork() -> None:
        ready.clear()
        release.clear()
        thread = Thread(target=hold_renderer_lock, daemon=True)
        threads.append(thread)
        thread.start()
        ready.wait()

    def after_fork_parent() -> None:
        release.set()
        threads.pop().join()

    # Acquire only at fork time so the parent's segmentation can finish. The
    # parent releases its copy afterward; the child's owner thread is gone.
    # No reversal worker or PyAV operation is replaced by a test double.
    os.register_at_fork(before=before_fork, after_in_parent=after_fork_parent)


class ReversalDeadlock(Slide):
    """A small slide that forces the inherited-lock condition from the reports."""

    max_duration_before_split_reverse = 1.0
    num_processes = 2
    disable_caching = True

    def construct(self) -> None:
        install_inherited_renderer_lock()
        dot = Dot().shift(LEFT)
        self.add(dot)
        # Separate animations supply keyframes at each segment boundary.
        for direction in (RIGHT, LEFT, RIGHT):
            self.play(dot.animate.shift(2 * direction), run_time=1)
        self.next_slide()


def reproduce(src: Path, dest: Path, num_processes: int) -> None:
    install_inherited_renderer_lock()
    reverse_video_file(
        src, dest, max_segment_duration=1.0, num_processes=num_processes, disable=True
    )
    assert multiprocessing.get_start_method() == "fork"


if __name__ == "__main__":
    reproduce(Path(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3]))
