"""
Utilities for using Manim Slides with IPython (in particular: Jupyter notebooks).
=================================================================================

.. toctree::
    :hidden:

    magic_example


.. note::

    The current implementation is highly inspired from Manim's own
    IPython magics, from v0.17.3.

This magic requires two additional dependencies: ``manim`` and ``IPython``.
You can install them manually, or with the extra keyword:

.. code-block:: bash

    pip install "manim-slides[magic]"

Note that you will still need to install Manim's platform-specific dependencies,
see
`their installation page <https://docs.manim.community/en/stable/installation.html>`_.
"""

from __future__ import annotations

import logging
import mimetypes
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from IPython import get_ipython
from IPython.core.interactiveshell import InteractiveShell
from IPython.core.magic import Magics, line_cell_magic, magics_class, needs_local_scope
from IPython.display import HTML, display
from manim import config, logger, tempconfig
from manim.__main__ import main
from manim.constants import RendererType
from manim.renderer.shader import shader_program_cache

from ..convert import RevealJS
from ..present import get_scenes_presentation_config


@magics_class
class ManimSlidesMagic(Magics):  # type: ignore
    def __init__(self, shell: InteractiveShell) -> None:
        super().__init__(shell)
        self.rendered_files: dict[Path, Path] = {}

    @needs_local_scope
    @line_cell_magic
    def manim_slides(  # noqa: C901
        self,
        line: str,
        cell: str | None = None,
        local_ns: dict[str, Any] | None = None,
    ) -> None:
        r"""
        Render Manim Slides contained in IPython cells. Works as a line or cell magic.

        .. note::

            This magic works pretty much like the one from Manim, except that it
            will render Manim Slides using RevealJS. For passing arguments to
            Manim Slides' convert module, use ``-manim-slides key=value``.

            Everything that is after ``--manim-slides`` will be send to
            Manim Slides' command. E.g., use ``--manim-slides controls=true``
            to display control buttons.

        .. hint::

            This line and cell magic works best when used in a JupyterLab
            environment: while all of the functionality is available for
            classic Jupyter notebooks as well, it is possible that videos
            sometimes don't update on repeated execution of the same cell
            if the scene name stays the same.

            This problem does not occur when using JupyterLab.

        Please refer to `<https://jupyter.org/>`_ for more information about JupyterLab
        and Jupyter notebooks.

        Usage in line mode::

            %manim_slides [CLI options] MyAwesomeSlide

        Usage in cell mode::

            %%manim_slides [CLI options] MyAwesomeSlide

            class MyAweseomeSlide(Slide):
                def construct(self):
                    ...

        Run ``%manim_slides --help`` and ``%manim_slides render --help``
        for possible command line interface options.

        .. note::

            The maximal width of the rendered videos that are displayed in the notebook can be
            configured via the ``media_width`` configuration option. The default is set to ``25vw``,
            which is 25% of your current viewport width. To allow the output to become as large
            as possible, set ``config.media_width = "100%"``.

            The ``media_embed`` option will embed the image/video output in the notebook. This is
            generally undesirable as it makes the notebooks very large, but is required on some
            platforms (notably Google's CoLab, where it is automatically enabled unless suppressed
            by ``config.embed = False``) and needed in cases when the notebook (or converted HTML
            file) will be moved relative to the video locations. Use-cases include building
            documentation with Sphinx and JupyterBook. See also the
            :mod:`Manim Slides directive for Sphinx
            <manim_slides.docs.manim_slides_directive>`.

        Examples
        --------
        First make sure to put ``from manim_slides import ManimSlidesMagic``,
        or even ``from manim_slides import *``
        in a cell and evaluate it. Then, a typical Jupyter notebook cell for Manim Slides
        could look as follows::

            %%manim_slides -v WARNING --progress_bar None MySlide --manim-slides controls=true one_file=true

            class MySlide(Slide):
                def construct(self):
                    square = Square()
                    circle = Circle()

                    self.play(Create(square))
                    self.next_slide()
                    self.play(Transform(square, circle))

        Evaluating this cell will render and display the ``MySlide`` slide
        defined in the body of the cell.

        .. note::

            In case you want to hide the red box containing the output progress bar, the ``progress_bar`` config
            option should be set to ``None``. This can also be done by passing ``--progress_bar None`` as a
            CLI flag.

        """
        if local_ns is None:
            local_ns = {}
        if cell:
            exec(cell, local_ns)

        split_args = line.split("--manim-slides", 2)
        manim_args = split_args[0].split()

        if len(split_args) == 2:
            manim_slides_args = split_args[1].split()
        else:
            manim_slides_args = []

        args = manim_args
        if not len(args) or "-h" in args or "--help" in args or "--version" in args:
            main(args, standalone_mode=False, prog_name="manim")
            return

        modified_args = self.add_additional_args(args)
        args = main(modified_args, standalone_mode=False, prog_name="manim")
        with tempconfig(local_ns.get("config", {})):
            config.digest_args(args)
            logging.getLogger("manim-slides").setLevel(logging.getLogger("manim").level)

            renderer = None
            if config.renderer == RendererType.OPENGL:
                from manim.renderer.opengl_renderer import OpenGLRenderer

                renderer = OpenGLRenderer()

            try:
                scene_cls = local_ns[config["scene_names"][0]]
                scene = scene_cls(renderer=renderer)
                scene.render()
            finally:
                # Shader cache becomes invalid as the context is destroyed
                shader_program_cache.clear()

                # Close OpenGL window here instead of waiting for the main thread to
                # finish causing the window to stay open and freeze
                if renderer is not None and renderer.window is not None:
                    renderer.window.close()

            if config["output_file"] is None:
                logger.info("No output file produced")
                return

            local_path = Path(config["output_file"]).relative_to(Path.cwd())
            tmpfile = (
                Path(config["media_dir"]) / "jupyter" / f"{_generate_file_name()}.html"
            )

            if local_path in self.rendered_files:
                self.rendered_files[local_path].unlink()
                pass
            self.rendered_files[local_path] = tmpfile
            tmpfile.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(local_path, tmpfile)

            file_type = mimetypes.guess_type(config["output_file"])[0] or "video/mp4"
            embed = config["media_embed"]
            if embed is None:
                # videos need to be embedded when running in google colab.
                # do this automatically in case config.media_embed has not been
                # set explicitly.
                embed = "google.colab" in str(get_ipython())

            if not file_type.startswith("video"):
                raise ValueError(
                    f"Manim Slides only supports video files, not {file_type}"
                )

            clsname = config["scene_names"][0]

            kwargs = dict(arg.split("=", 1) for arg in manim_slides_args)

            # If data_uri is set, raise a warning
            if "data_uri" in kwargs:
                logger.warning(
                    "'data_uri' configuration option is deprecated and will be removed in a future release. "
                    "Please use 'one_file' instead."
                )
                kwargs["one_file"] = (
                    kwargs["one_file"]
                    if "one_file" in kwargs
                    else kwargs.pop("data_uri")
                )

            if embed:  # Embedding implies one_file
                kwargs["one_file"] = "true"

            # TODO: FIXME
            # Seems like files are blocked so one_file is the only working option...
            if kwargs.get("one_file", "false").lower().strip() == "false":
                logger.warning(
                    "one_file option is currently automatically enabled, "
                    "because using local video files does not seem to work properly."
                )
                kwargs["one_file"] = "true"

            presentation_configs = get_scenes_presentation_config(
                [clsname], Path("./slides")
            )
            RevealJS(presentation_configs=presentation_configs, **kwargs).convert_to(
                tmpfile
            )

            if embed:
                result = HTML(
                    """<div style="position:relative;padding-bottom:56.25%;"><iframe style="width:100%;height:100%;position:absolute;left:0px;top:0px;" frameborder="0" width="100%" height="100%" allowfullscreen allow="autoplay" srcdoc="{srcdoc}"></iframe></div>""".format(
                        srcdoc=tmpfile.read_text().replace('"', "'")
                    )
                )
            else:
                result = HTML(
                    f"""<div style="position:relative;padding-bottom:56.25%;"><iframe style="width:100%;height:100%;position:absolute;left:0px;top:0px;" frameborder="0" width="100%" height="100%" allowfullscreen allow="autoplay" src="{tmpfile.as_posix()}"></iframe></div>"""
                )

            display(result)

    def add_additional_args(self, args: list[str]) -> list[str]:
        additional_args = ["--jupyter"]
        # Use webm to support transparency
        if "-t" in args and "--format" not in args:
            additional_args += ["--format", "webm"]
        return additional_args + args[:-1] + [""] + [args[-1]]


def _generate_file_name() -> str:
    return config["scene_names"][0] + "@" + datetime.now().strftime("%Y-%m-%d@%H-%M-%S")  # type: ignore
