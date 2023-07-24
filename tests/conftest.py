from pathlib import Path
from typing import Iterator

import pytest

from manim_slides.logger import make_logger

_ = make_logger()  # This is run so that "PERF" level is created


@pytest.fixture
def folder_path() -> Iterator[Path]:
    yield (Path(__file__).parent / "slides").resolve()
