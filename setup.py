# type: ignore
import importlib.util
import os
import sys

import setuptools

if sys.version_info < (3, 7):
    raise RuntimeError("This package requires Python 3.7+")

spec = importlib.util.spec_from_file_location(
    "__version__", os.path.join("manim_slides", "__version__.py")
)
version = importlib.util.module_from_spec(spec)
spec.loader.exec_module(version)


with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
    name="manim-slides",
    version=version.__version__,
    author="Jérome Eertmans (previously, Federico A. Galatolo)",
    author_email="jeertmans@icloud.com (resp., federico.galatolo@ing.unipi.it)",
    description="Tool for live presentations using manim",
    url="https://github.com/jeertmans/manim-slides",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    entry_points={
        "console_scripts": [
            "manim-slides=manim_slides.main:cli",
        ],
    },
    python_requires=">=3.7",
    install_requires=[
        "click>=8.0",
        "click-default-group>=1.2",
        "numpy>=1.19.3",
        "pydantic>=1.9.1",
        "pyqt5>=5.15",
        "opencv-python>=4.6",
        "tqdm>=4.62.3",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
)
