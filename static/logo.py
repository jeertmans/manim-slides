# flake8: noqa: F403, F405
# type: ignore
import os

from manim import *

THEME = os.environ.get("MANIM_SLIDES_THEME", "light").lower().replace("_", "-")


class ManimSlidesLogo(Scene):
    def construct(self):
        tex_template = TexTemplate()
        tex_template.add_to_preamble(r"\usepackage{graphicx}\usepackage{fontawesome5}")
        self.camera.background_color = {
            "light": "#ffffff",
            "dark-docs": "#131416",
            "dark-github": "#0d1117",
        }[THEME]
        logo_green = "#87c2a5"
        logo_blue = "#525893"
        logo_red = "#e07a5f"
        logo_black = {
            "light": "#343434",
            "dark-docs": "#d0d0d0",
            "dark-github": "#c9d1d9",
        }[THEME]
        ds_m = MathTex(r"\mathbb{M}", fill_color=logo_black).scale(7)
        ds_m.shift(2.25 * LEFT + 1.5 * UP)
        slides = MathTex(r"\mathbb{S}\text{lides}", fill_color=logo_black).scale(4)
        slides.next_to(ds_m, DOWN)
        slides.shift(DOWN)
        play = Tex(
            r"\faStepBackward\faStepForward",
            fill_color=logo_black,
            tex_template=tex_template,
        ).scale(4)
        play.next_to(ds_m, LEFT)
        play.shift(LEFT + 0.5 * DOWN)
        comment = Tex(
            r"\reflectbox{\faComment*[regular]}",
            fill_color=logo_black,
            tex_template=tex_template,
        ).scale(9)
        comment.move_to(play)
        comment.shift(0.4 * DOWN)
        circle = Circle(color=logo_green, fill_opacity=1).shift(LEFT)
        square = Square(color=logo_blue, fill_opacity=1).shift(UP)
        triangle = Triangle(color=logo_red, fill_opacity=1).shift(RIGHT)
        logo = VGroup(
            triangle, square, circle, ds_m, slides, comment, play
        )  # order matters
        logo.move_to(ORIGIN)
        self.add(logo)


class ManimSlidesFavicon(Scene):
    def construct(self):
        tex_template = TexTemplate()
        tex_template.add_to_preamble(r"\usepackage{graphicx}\usepackage{fontawesome5}")
        fill_color = "#c9d1d9"
        stroke_color = "#343434"
        play = Tex(
            r"\faStepBackward\faStepForward",
            fill_color=fill_color,
            stroke_color=stroke_color,
            tex_template=tex_template,
        ).scale(4)
        comment = Tex(
            r"\reflectbox{\faComment*[regular]}",
            fill_color=fill_color,
            stroke_color=stroke_color,
            tex_template=tex_template,
        ).scale(9)
        comment.move_to(play)
        comment.shift(0.4 * DOWN)
        favicon = VGroup(comment, play).scale(3)
        favicon.move_to(ORIGIN)
        self.add(favicon)
