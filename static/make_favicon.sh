#! /bin/bash

uv run manim-slides render -t -qk -s --format png --resolution 64,64 static/logo.py ManimSlidesFavicon && mv media/images/logo/*.png static/favicon.png

ln -f -r -s static/favicon.png docs/source/_static/favicon.png
