import random
import string
from pathlib import Path
from typing import Generator, Iterator, List

import pytest

from manim_slides.config import PresentationConfig


@pytest.fixture
def tests_folder() -> Iterator[Path]:
    path = Path(__file__)
    assert path.exists(), f"Path {path} does not exist!"
    yield path


@pytest.fixture
def project_folder(tests_folder: Path) -> Iterator[Path]:
    path = tests_folder.parent
    assert path.exists(), f"Path {path} does not exist!"
    yield path


@pytest.fixture
def data_folder(tests_folder: Path) -> Iterator[Path]:
    path = (tests_folder / "data")
    assert path.exists(), f"Path {path} does not exist!"
    yield path


@pytest.fixture
def slides_folder(data_folder: Path) -> Iterator[Path]:
    path = (data_folder / "slides")
    assert path.exists(), f"Path {path} does not exist!"
    yield path


@pytest.fixture
def slides_file(data_folder: Path) -> Iterator[Path]:
    path = (data_folder / "slides.py")
    assert path.exists(), f"Path {path} does not exist!"
    yield path


@pytest.fixture
def manimgl_config(project_folder: Path) -> Iterator[Path]:
    path = (project_folder / "custom_config.yml")
    assert path.exists(), f"Path {path} does not exist!"
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
