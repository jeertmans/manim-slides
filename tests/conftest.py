import random
import string
from pathlib import Path
from typing import Generator, Iterator, List

import pytest

from manim_slides.config import PresentationConfig
from manim_slides.logger import make_logger

_ = make_logger()  # This is run so that logger is created


@pytest.fixture
def data_folder() -> Iterator[Path]:
    path = (Path(__file__).parent / "data").resolve()
    assert path.exists()
    yield path


@pytest.fixture
def slides_folder(data_folder: Path) -> Iterator[Path]:
    path = (data_folder / "slides").resolve()
    assert path.exists()
    yield path


@pytest.fixture
def slides_file(data_folder: Path) -> Iterator[Path]:
    path = (data_folder / "slides.py").resolve()
    assert path.exists()
    yield path


def random_path(
    length: int = 20,
    dirname: Path = Path("./media/videos/example"),
    suffix: str = ".mp4",
    touch: bool = False,
) -> Path:
    basename = "".join(random.choices(string.ascii_letters, k=length))

    filepath = dirname.joinpath(basename + suffix)

    if touch:
        filepath.touch()

    return filepath


@pytest.fixture
def paths() -> Generator[List[Path], None, None]:
    random.seed(1234)

    yield [random_path() for _ in range(20)]


@pytest.fixture
def presentation_config(
    slides_folder: Path,
) -> Generator[PresentationConfig, None, None]:
    yield PresentationConfig.from_file(slides_folder / "BasicSlide.json")
