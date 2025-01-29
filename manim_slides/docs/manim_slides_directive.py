# type: ignore
r"""
A directive for including Manim Slides in a Sphinx document
===========================================================

.. warning::

    This Sphinx extension requires Manim to be installed,
    and won't probably work on ManimGL examples.

.. note::

    The current implementation is highly inspired from Manim's own
    sphinx directive, from v0.17.3.

When rendering the HTML documentation, the ``.. manim-slides::``
directive implemented here allows to include rendered videos.

This directive requires three additional dependencies:
``manim``, ``docutils`` and ``jinja2``. The last two are usually bundled
with Sphinx.
You can install them manually, or with the extra keyword:

.. code-block:: bash

    pip install "manim-slides[sphinx-directive]"

Note that you will still need to install Manim's platform-specific dependencies,
see
`their installation page <https://docs.manim.community/en/stable/installation.html>`_.

Usage
-----

First, you must include the directive in the Sphinx configuration file:

.. code-block:: python
    :caption: Sphinx configuration file (usually :code:`docs/source/conf.py`).
    :emphasize-lines: 3

    extensions = [
        # ...
        "manim_slides.docs.manim_slides_directive",
    ]

Its basic usage that allows processing **inline content**
looks as follows::

    .. manim-slides:: MySlide
        from manim import *
        from manim_slides import Slide

        class MySlide(Slide):
            def construct(self):
                ...

It is required to pass the name of the class representing the
scene to be rendered to the directive.

As a second application, the directive can also be used to
render scenes that are defined within doctests, for example::

    .. manim-slides:: DirectiveDoctestExample
        :ref_classes: Dot

        >>> from manim import Create, Dot, RED
        >>> from manim_slides import Slide
        >>> dot = Dot(color=RED)
        >>> dot.color
        <Color #fc6255>
        >>> class DirectiveDoctestExample(Slide):
        ...     def construct(self):
        ...         self.play(Create(dot))
        ...

A third application is to render scenes from another specific file::

    .. manim-slides:: file.py:FileExample
        :hide_source:
        :quality: high

.. warning::

    The code will be executed with the current working directory
    being the same as the one containing the source file. This being said,
    you should probably not include examples that rely on external files, since
    relative paths risk to be broken.

.. note::

    If you want to skip rendering the slides (e.g., for testing)
    you can either set the ``SKIP_MANIM_SLIDES`` environ
    variable (to any value) or pass  the ``skip-manim-slides``
    tag to ``sphinx``:

    .. code-block:: bash

        sphinx-build -t skip-manim-slides <OTHER_SPHINX_OPTIONS>
        # or if you use a Makefile
        make html O=-tskip-manim-slides

Options
-------

Options can be passed as follows::

    .. manim-slides:: <file>:<Class name>
        :<option name>: <value>

The following configuration options are supported by the
directive:

    hide_source
        If this flag is present without argument,
        the source code is not displayed above the rendered video.

    quality : {'low', 'medium', 'high', 'fourk'}
        Controls render quality of the video, in analogy to
        the corresponding command line flags.

    ref_classes
        A list of classes, separated by spaces, that is
        rendered in a reference block after the source code.

    ref_functions
        A list of functions, separated by spaces,
        that is rendered in a reference block after the source code.

    ref_methods
        A list of methods, separated by spaces,
        that is rendered in a reference block after the source code.

    template
        A path to the template file to use.

    config_options
        An unprocessed string of options to pass to ``manim-slides convert``.
        Options must be separated with a space, and each option must be
        a key, value pair using an equal sign as a separator.

        Unlike for the CLI version, you don't need to prepend each option with
        ``-c``.

        E.g., pass ``slide_number=true controls=false``.

        By default, ``controls=true`` is set.

Examples
--------
The following code::

    .. manim-slides:: MySlide
        :hide_source:
        :config_options: slide_number=true controls=false

        from manim import *
        from manim_slides import Slide

        class MySlide(Slide):
            def construct(self):
                text = Text("Hello")
                self.wipe([], text)

                self.next_slide()
                self.play(text.animate.scale(2))

                self.next_slide()
                self.zoom(text)

Renders as follows:

.. manim-slides:: MySlide
    :hide_source:
    :config_options: slide_number=true controls=false

    from manim import *
    from manim_slides import Slide

    class MySlide(Slide):
        def construct(self):
            text = Text("Hello")
            self.wipe([], text)

            self.next_slide()
            self.play(text.animate.scale(2))

            self.next_slide()
            self.zoom(text)


"""  # noqa: D400, D415

from __future__ import annotations

import csv
import itertools as it
import os
import re
import shlex
import sys
from pathlib import Path
from timeit import timeit

import jinja2
from docutils import nodes
from docutils.parsers.rst import Directive, directives
from docutils.statemachine import StringList
from manim import QUALITIES

from ..convert import RevealJS
from ..present import get_scenes_presentation_config

classnamedict = {}


class SkipManimNode(nodes.Admonition, nodes.Element):
    """
    Auxiliary node class that is used when the ``skip-manim-slides`` tag is present or
    ``.pot`` files are being built.

    Skips rendering the manim-slides directive and outputs a placeholder instead.
    """

    pass


def visit(self, node, name=""):
    self.visit_admonition(node, name)
    if not isinstance(node[0], nodes.title):
        node.insert(0, nodes.title("skip-manim-slides", "Example Placeholder"))


def depart(self, node):
    self.depart_admonition(node)


def process_name_list(option_input: str, reference_type: str) -> list[str]:
    r"""
    Reformats a string of space separated class names as a list of strings containing
    valid Sphinx references.

    Tests
    -----

    ::

        >>> process_name_list("Tex TexTemplate", "class")
        [':class:`~.Tex`', ':class:`~.TexTemplate`']
        >>> process_name_list("Scene.play Mobject.rotate", "func")
        [':func:`~.Scene.play`', ':func:`~.Mobject.rotate`']
    """
    return [f":{reference_type}:`~.{name}`" for name in option_input.split()]


class ManimSlidesDirective(Directive):
    r"""
    The manim-slides directive, rendering videos while building the documentation.

    See the module docstring for documentation.
    """

    has_content = True
    required_arguments = 1
    optional_arguments = 0
    option_spec = {  # noqa: RUF012
        "hide_source": bool,
        "quality": lambda arg: directives.choice(
            arg,
            ("low", "medium", "high", "fourk"),
        ),
        "ref_modules": lambda arg: process_name_list(arg, "mod"),
        "ref_classes": lambda arg: process_name_list(arg, "class"),
        "ref_functions": lambda arg: process_name_list(arg, "func"),
        "ref_methods": lambda arg: process_name_list(arg, "meth"),
        "template": lambda arg: Path(arg),
        "config_options": lambda arg: dict(
            option.split("=") for option in shlex.split(arg)
        ),
    }
    final_argument_whitespace = True

    def run(self):  # noqa: C901
        # Rendering is skipped if the tag skip-manim is present,
        # or if we are making the pot-files
        should_skip = (
            self.state.document.settings.env.app.builder.tags.has("skip-manim-slides")
            or self.state.document.settings.env.app.builder.name == "gettext"
            or "SKIP_MANIM_SLIDES" in os.environ
        )
        if should_skip:
            node = SkipManimNode()
            self.state.nested_parse(
                StringList(
                    [
                        f"Placeholder block for ``{self.arguments[0]}``.",
                        "",
                        ".. code-block:: python",
                        "",
                    ]
                    + ["    " + line for line in self.content]
                ),
                self.content_offset,
                node,
            )
            return [node]

        from manim import config, tempconfig

        global classnamedict

        def split_file_cls(arg: str) -> tuple[Path, str]:
            if ":" in arg:
                file, cls = arg.split(":", maxsplit=1)
                _, file = self.state.document.settings.env.relfn2path(file)
                return Path(file), cls
            else:
                return None, arg

        arguments = [split_file_cls(arg) for arg in self.arguments]

        clsname = arguments[0][1]
        if clsname not in classnamedict:
            classnamedict[clsname] = 1
        else:
            classnamedict[clsname] += 1

        hide_source = "hide_source" in self.options

        ref_content = (
            self.options.get("ref_modules", [])
            + self.options.get("ref_classes", [])
            + self.options.get("ref_functions", [])
            + self.options.get("ref_methods", [])
        )
        if ref_content:
            ref_block = "References: " + " ".join(ref_content)

        else:
            ref_block = ""

        if "quality" in self.options:
            quality = f"{self.options['quality']}_quality"
        else:
            quality = "example_quality"
        frame_rate = QUALITIES[quality]["frame_rate"]
        pixel_height = QUALITIES[quality]["pixel_height"]
        pixel_width = QUALITIES[quality]["pixel_width"]

        state_machine = self.state_machine
        document = state_machine.document

        source_file_name = Path(document.attributes["source"])
        source_rel_name = source_file_name.relative_to(setup.confdir)
        source_rel_dir = source_rel_name.parents[0]
        dest_dir = Path(setup.app.builder.outdir, source_rel_dir).absolute()
        if not dest_dir.exists():
            dest_dir.mkdir(parents=True, exist_ok=True)

        source_block = [
            ".. code-block:: python",
            "",
            *("    " + line for line in self.content),
        ]
        source_block = "\n".join(source_block)

        config.media_dir = (Path(setup.confdir) / "media").absolute()
        config.images_dir = "{media_dir}/images"
        config.video_dir = "{media_dir}/videos/{quality}"
        output_file = f"{clsname}-{classnamedict[clsname]}"
        config.assets_dir = Path("_static")
        config.progress_bar = "none"
        config.verbosity = "WARNING"

        example_config = {
            "frame_rate": frame_rate,
            "pixel_height": pixel_height,
            "pixel_width": pixel_width,
            "output_file": output_file,
        }

        if file := arguments[0][0]:
            user_code = file.absolute().read_text().splitlines()
        else:
            user_code = self.content

        if user_code[0].startswith(">>> "):  # check whether block comes from doctest
            user_code = [
                line[4:] for line in user_code if line.startswith((">>> ", "... "))
            ]

        code = [
            *user_code,
            f"{clsname}().render()",
        ]

        try:
            with tempconfig(example_config):
                print(f"Rendering {clsname}...")  # noqa: T201
                run_time = timeit(lambda: exec("\n".join(code), globals()), number=1)
                video_dir = config.get_dir("video_dir")
        except Exception as e:
            raise RuntimeError(f"Error while rendering example {clsname}") from e

        _write_rendering_stats(
            clsname,
            run_time,
            self.state.document.settings.env.docname,
        )

        # copy video file to output directory
        filename = f"{output_file}.html"
        filesrc = video_dir / filename
        destfile = Path(dest_dir, filename)
        presentation_configs = get_scenes_presentation_config(
            [clsname], Path("./slides")
        )

        template = self.options.get("template", None)

        if template:
            template = source_file_name.parents[0].joinpath(template)

        config_options = self.options.get("config_options", {})
        config_options.setdefault("controls", "true")

        RevealJS(
            presentation_configs=presentation_configs,
            template=template,
            **config_options,
        ).convert_to(destfile)

        rendered_template = jinja2.Template(TEMPLATE).render(
            clsname=clsname,
            clsname_lowercase=clsname.lower(),
            hide_source=hide_source,
            filesrc_rel=Path(filesrc).relative_to(setup.confdir).as_posix(),
            output_file=output_file,
            source_block=source_block,
            ref_block=ref_block,
        )
        state_machine.insert_input(
            rendered_template.split("\n"),
            source=document.attributes["source"],
        )

        return []


rendering_times_file_path = Path("../rendering_times.csv")


def _write_rendering_stats(scene_name, run_time, file_name):
    with rendering_times_file_path.open("a") as file:
        csv.writer(file).writerow(
            [
                re.sub(r"^(reference\/)|(manim\.)", "", file_name),
                scene_name,
                f"{run_time:.3f}",
            ],
        )


def _log_rendering_times(*args):
    if rendering_times_file_path.exists():
        with rendering_times_file_path.open() as file:
            data = list(csv.reader(file))
        if len(data) == 0:
            sys.exit()

        print("\nRendering Summary\n-----------------\n")  # noqa: T201

        max_file_length = max(len(row[0]) for row in data)
        for key, group in it.groupby(data, key=lambda row: row[0]):
            key = key.ljust(max_file_length + 1, ".")
            group = list(group)
            if len(group) == 1:
                row = group[0]
                print(f"{key}{row[2].rjust(7, '.')}s {row[1]}")  # noqa: T201
                continue
            time_sum = sum(float(row[2]) for row in group)
            print(  # noqa: T201
                f"{key}{f'{time_sum:.3f}'.rjust(7, '.')}s  => {len(group)} EXAMPLES",
            )
            for row in group:
                print(  # noqa: T201
                    f"{' ' * (max_file_length)} {row[2].rjust(7)}s {row[1]}"
                )
        print("")  # noqa: T201


def _delete_rendering_times(*args):
    if rendering_times_file_path.exists():
        rendering_times_file_path.unlink()


def setup(app):
    app.add_node(SkipManimNode, html=(visit, depart))

    setup.app = app
    setup.config = app.config
    setup.confdir = app.confdir

    app.add_directive("manim-slides", ManimSlidesDirective)

    app.connect("builder-inited", _delete_rendering_times)
    app.connect("build-finished", _log_rendering_times)

    metadata = {"parallel_read_safe": False, "parallel_write_safe": True}
    return metadata


TEMPLATE = r"""
{% if not hide_source %}
.. raw:: html

    <div id="{{ clsname_lowercase }}" class="admonition admonition-manim-example">
    <p class="admonition-title">Example: {{ clsname }} <a class="headerlink" href="#{{ clsname_lowercase }}">¶</a></p>

{% endif %}


.. raw:: html

    <!-- From: https://faq.dailymotion.com/hc/en-us/articles/360022841393-How-to-preserve-the-player-aspect-ratio-on-a-responsive-page -->

    <div style="position:relative;padding-bottom:56.25%;">
        <iframe
            style="width:100%;height:100%;position:absolute;left:0px;top:0px;"
            frameborder="0"
            width="100%"
            height="100%"
            allowfullscreen
            allow="autoplay"
            src="./{{ output_file }}.html">
        </iframe>
    </div>

{% if not hide_source %}
{{ source_block }}

{{ ref_block }}

.. raw:: html

    </div>

{% endif %}
"""
