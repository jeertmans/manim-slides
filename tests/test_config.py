import random
import string
import tempfile
from pathlib import Path
from typing import Any, Generator, List

import pytest
from pydantic import ValidationError

from manim_slides.config import Key, merge_basenames, PresentationConfig, SlideConfig, SlideType


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
def presentation_config(paths: List[Path]) -> Generator[PresentationConfig, None, None]:
    dirname = Path(tempfile.mkdtemp())
    files = [random_path(dirname=dirname, touch=True) for _ in range(10)]

    slides = [
            SlideConfig(
                type=SlideType.slide,
                start_animation=0,
                end_animation=5,
                number=1,
            ),
            SlideConfig(
                type=SlideType.loop,
                start_animation=5,
                end_animation=6,
                number=2,
            ),
            SlideConfig(
                type=SlideType.last,
                start_animation=6,
                end_animation=10,
                number=3,
            ),
    ]

    yield PresentationConfig(
            slides=slides,
            files=files,
    )

def test_merge_basenames(paths: List[Path]) -> None:
    path = merge_basenames(paths)
    assert path.suffix == paths[0].suffix
    assert path.parent == paths[0].parent


class TestKey:
    @pytest.mark.parametrize(("ids", "name"), [([1], None), ([1], "some key name")])
    def test_valid_keys(self, ids: Any, name: Any) -> None:
        _ = Key(ids=ids, name=name)

    @pytest.mark.parametrize(
        ("ids", "name"), [([], None), ([-1], None), ([1], {"an": " invalid name"})]
    )
    def test_invalid_keys(self, ids: Any, name: Any) -> None:
        with pytest.raises(ValidationError):
            _ = Key(ids=ids, name=name)


class TestPresentationConfig:

    def test_bump_to_json(self, presentation_config: PresentationConfig) -> None:
        _ = presentation_config.model_dump_json(indent=2)
