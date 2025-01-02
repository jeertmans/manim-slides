# type: ignore
# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import sys
from datetime import date

from manim_slides import __version__

assert sys.version_info >= (3, 10), "Building docs requires Python 3.10"

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "Manim Slides"
copyright = f"2024-{date.today().year}, Jérome Eertmans"
author = "Jérome Eertmans"
version = __version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    # Built-in
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    # Additional
    "nbsphinx",
    "myst_parser",
    "sphinxcontrib.programoutput",
    "sphinxext.opengraph",
    "sphinx_click",
    "sphinx_copybutton",
    "sphinx_design",
    # Custom
    "manim_slides.docs.manim_slides_directive",
]

autodoc_typehints = "both"

myst_enable_extensions = [
    "colon_fence",
    "html_admonition",
]

templates_path = ["_templates"]
exclude_patterns = []

# Removes the 'package.module' part from package.module.Class
add_module_names = False

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = ["_static"]
html_favicon = "_static/favicon.png"

html_theme_options = {
    "light_logo": "logo_light_transparent.png",
    "dark_logo": "logo_dark_transparent.png",
    "footer_icons": [
        {
            "name": "GitHub",
            "url": "https://github.com/jeertmans/manim-slides",
            "html": """
                <svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 16 16">
                    <path fill-rule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z"></path>
                </svg>
            """,
            "class": "",
        },
    ],
    "source_repository": "https://github.com/jeertmans/manim-slides/",
    "source_branch": "main",
    "source_directory": "docs/source/",
}

# -- Intersphinx mapping

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "manim": ("https://docs.manim.community/en/stable/", None),
    "manimlib": ("https://3b1b.github.io/manim/", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
}

# -- OpenGraph settings

ogp_site_url = "https://eertmans.be/manim-slides/"
ogp_use_first_image = True
