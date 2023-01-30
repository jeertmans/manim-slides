# Internals

Manim-Slides' work in split in two steps: first, when rendering animation, and, second, when converting multiple animations into one slides presentation.

## Rendering

To render animations, Manim Slides simply uses Manim or ManimGL, and creates some additional output files that it needs for the presentation.

## Slides presentation

Manim Slides searches for the local artifacts it generated previously, and concatenates them into one presentation. For the graphical interface, it uses `PySide6`.
