import random
import string
from collections.abc import Generator, Iterator
from pathlib import Path

import pytest

from manim_slides.config import PresentationConfig


@pytest.fixture(scope="session")
def tests_folder() -> Iterator[Path]:
    yield Path(__file__).parent.resolve(strict=True)


@pytest.fixture(scope="session")
def project_folder(tests_folder: Path) -> Iterator[Path]:
    yield tests_folder.parent.resolve(strict=True)


@pytest.fixture(scope="session")
def data_folder(tests_folder: Path) -> Iterator[Path]:
    yield (tests_folder / "data").resolve(strict=True)


@pytest.fixture(scope="session")
def slides_folder(data_folder: Path) -> Iterator[Path]:
    yield (data_folder / "slides").resolve(strict=True)


@pytest.fixture(scope="session")
def slides_file(data_folder: Path) -> Iterator[Path]:
    yield (data_folder / "slides.py").resolve(strict=True)


@pytest.fixture(scope="session")
def manimgl_config(project_folder: Path) -> Iterator[Path]:
    yield (project_folder / "custom_config.yml").resolve(strict=True)


@pytest.fixture(scope="session")
def video_file(data_folder: Path) -> Iterator[Path]:
    yield (data_folder / "video.mp4").resolve(strict=True)


@pytest.fixture(scope="session")
def video_data_uri_file(data_folder: Path) -> Iterator[Path]:
    yield (data_folder / "video_data_uri.txt").resolve(strict=True)


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

    return filepath.resolve(strict=touch)


@pytest.fixture
def paths() -> Generator[list[Path], None, None]:
    random.seed(1234)

    yield [random_path() for _ in range(20)]


@pytest.fixture
def presentation_config(
    slides_folder: Path,
) -> Generator[PresentationConfig, None, None]:
    yield PresentationConfig.from_file(slides_folder / "BasicSlide.json")


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Make sure missing modules run at the very end."""

    def uses_missing_modules_fixtures(item: pytest.Item) -> int:
        if "missing_modules" in getattr(item, "fixturenames", []):
            return 1

        return 0

    items.sort(key=uses_missing_modules_fixtures)
