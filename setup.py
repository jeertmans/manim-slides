import setuptools
import os

with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "README.md"), "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="manim_presentation",
    version="0.2.0",
    author="Federico A. Galatolo",
    author_email="federico.galatolo@ing.unipi.it",
    description="Tool for live presentations using manim",
    url="https://github.com/galatolofederico/manim-presentation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    entry_points = {
        "console_scripts": ["manim_presentation=manim_presentation.present:main"],
    },
    install_requires=[
    ],
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta"
    ],
)