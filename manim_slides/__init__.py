# flake8: noqa: F401
import sys
from types import ModuleType
from typing import Any, List

from .__version__ import __version__


class module(ModuleType):
    def __getattr__(self, name: str) -> Any:
        if name == "Slide" or name == "ThreeDSlide":
            module = __import__(
                "manim_slides.slide", None, None, ["Slide", "ThreeDSlide"]
            )
            return getattr(module, name)

        return ModuleType.__getattribute__(self, name)

    def __dir__(self) -> List[str]:
        result = list(new_module.__all__)
        result.extend(
            (
                "__file__",
                "__doc__",
                "__all__",
                "__docformat__",
                "__name__",
                "__path__",
                "__package__",
                "__version__",
            )
        )
        return result


old_module = sys.modules["manim_slides"]
new_module = sys.modules["manim_slides"] = module("manim_slides")

new_module.__dict__.update(
    {
        "__file__": __file__,
        "__package__": "manim_slides",
        "__path__": __path__,
        "__doc__": __doc__,
        "__version__": __version__,
        "__all__": ("__version__", "Slides", "ThreeDSlide"),
    }
)
