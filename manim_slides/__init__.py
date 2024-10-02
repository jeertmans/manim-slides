import sys
from types import ModuleType
from typing import Any

from .__version__ import __version__


class Module(ModuleType):
    def __getattr__(self, name: str) -> Any:
        if name == "Slide" or name == "ThreeDSlide":
            module = __import__(
                "manim_slides.slide", None, None, ["Slide", "ThreeDSlide"]
            )
            return getattr(module, name)
        elif name == "ManimSlidesMagic":
            module = __import__(
                "manim_slides.ipython.ipython_magic", None, None, ["ManimSlidesMagic"]
            )
            magic = getattr(module, name)

            from IPython import get_ipython

            ipy = get_ipython()

            if ipy is not None:
                ipy.register_magics(magic)

            return magic

        return ModuleType.__getattribute__(self, name)

    def __dir__(self) -> list[str]:
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
new_module = sys.modules["manim_slides"] = Module("manim_slides")

new_module.__dict__.update(
    {
        "__file__": __file__,
        "__package__": "manim_slides",
        "__path__": __path__,
        "__doc__": __doc__,
        "__version__": __version__,
        "__all__": ("__version__", "ManimSlidesMagic", "Slide", "ThreeDSlide"),
    }
)
