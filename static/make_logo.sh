#! /bin/bash

MANIM_SLIDES_THEME=light uv run manim-slides render -qk -s --format png --resolution 2560,1280 static/logo.py ManimSlidesLogo && mv media/images/logo/*.png static/logo.png

ln -f -r -s static/logo.png docs/source/_static/logo.png

MANIM_SLIDES_THEME=dark_docs uv run manim-slides render -qk -s --format png --resolution 2560,1280 static/logo.py ManimSlidesLogo && mv media/images/logo/*.png static/logo_dark_docs.png

ln -f -r -s static/logo_dark_docs.png docs/source/_static/logo_dark_docs.png

MANIM_SLIDES_THEME=dark_github uv run manim-slides render -qk -s --format png --resolution 2560,1280 static/logo.py ManimSlidesLogo && mv media/images/logo/*.png static/logo_dark_github.png

ln -f -r -s static/logo_dark_github.png docs/source/_static/logo_dark_github.png

MANIM_SLIDES_THEME=light uv run manim-slides render -t -qk -s --format png --resolution 2560,1280 static/logo.py ManimSlidesLogo && mv media/images/logo/*.png static/logo_light_transparent.png

ln -f -r -s static/logo_light_transparent.png docs/source/_static/logo_light_transparent.png

MANIM_SLIDES_THEME=dark_docs uv run manim-slides render -t -qk -s --format png --resolution 2560,1280 static/logo.py ManimSlidesLogo && mv media/images/logo/*.png static/logo_dark_transparent.png

ln -f -r -s static/logo_dark_transparent.png docs/source/_static/logo_dark_transparent.png
