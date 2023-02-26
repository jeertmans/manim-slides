#! /bin/bash

MANIM_SLIDES_THEME=light poetry run manim render -qk -s --format png --resolution 2560,1280 static/logo.py && mv media/images/logo/*.png static/logo.png

cp static/logo.png docs/source/_static/logo.png

MANIM_SLIDES_THEME=dark_docs poetry run manim render -qk -s --format png --resolution 2560,1280 static/logo.py && mv media/images/logo/*.png static/logo_dark_docs.png

cp static/logo_dark_docs.png docs/source/_static/logo_dark_docs.png

MANIM_SLIDES_THEME=dark_github poetry run manim render -qk -s --format png --resolution 2560,1280 static/logo.py && mv media/images/logo/*.png static/logo_dark_github.png

cp static/logo_dark_github.png docs/source/_static/logo_dark_github.png
