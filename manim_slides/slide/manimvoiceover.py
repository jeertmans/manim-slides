from contextlib import contextmanager
from typing import Generator

from .manim import Slide as ManimSlide
from manim import ThreeDScene
from manim_voiceover import VoiceoverScene, VoiceoverTracker


class Slide(ManimSlide, VoiceoverScene):
    """
    Inherits from :class:`Scene<manim.scene.scene.Scene>` and provide necessary tools
    for slides rendering.

    :param args: Positional arguments passed to scene object.
    :param output_folder: Where the slide animation files should be written.
    :param kwargs: Keyword arguments passed to scene object.
    :cvar bool disable_caching: :data:`False`: Whether to disable the use of
        cached animation files.
    :cvar bool flush_cache: :data:`False`: Whether to flush the cache.

        Unlike with Manim, flushing is performed before rendering.
    :cvar bool skip_reversing: :data:`False`: Whether to generate reversed animations.

        If set to :data:`False`, and no cached reversed animation
        exists (or caching is disabled) for a given slide,
        then the reversed animation will be simply the same
        as the original one, i.e., ``rev_file = file``,
        for the current slide config.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.slide_audio = {
            "starting_time": 0,
            "audio": [],
        }  # self._slides only defines the slide after next_slide() is called, so we need to define the slides here and then update them in next_slide().

    @contextmanager
    def voiceover(
        self, text: str, **kwargs
    ) -> Generator[
        VoiceoverTracker, None, None
    ]:  # This is taken straight from manim_voiceover.VoiceoverScene.voiceover just with the elimination of ssml as it is not implemented yet.
        """The main function to be used for adding voiceover to a scene.

        Args:
            text (str): The text to be spoken.

        Yields:
            Generator[VoiceoverTracker, None, None]: The voiceover tracker object.
        """
        try:
            voiceover_information = self.add_voiceover_text(text, **kwargs)
            yield voiceover_information
        finally:
            self.wait_for_voiceover()
            self.slide_audio["audio"].append(
                {
                    "ending_time": self.renderer.time,
                    "file": voiceover_information.data["final_audio"],
                }
            )

    def next_slide(self, *args, **kwargs):
        super().next_slide(*args, **kwargs)

        self.add_audio_to_slide()
        self.slide_audio = {
            "starting_time": self.renderer.time,
            "audio": [],
        }

    def _add_last_slide(self) -> None:
        super()._add_last_slide()
        self.add_audio_to_slide()

    def add_audio_to_slide(self):
        for audio in self.slide_audio["audio"]:
            self._slides[-1].audio.append(
                {
                    "starting_time": audio["ending_time"]
                    - self.slide_audio["starting_time"],
                    "file": f"./media/voiceovers/{audio['file']}",
                }
            )


class ThreeDSlide(Slide, ThreeDScene):  # type: ignore[misc]
    """
    Inherits from :class:`Slide` and
    :class:`ThreeDScene<manim.scene.three_d_scene.ThreeDScene>` and provide necessary
    tools for slides rendering.

    Examples
    --------
    .. manim-slides:: ThreeDExample

        from manim import *
        from manim_slides import ThreeDSlide

        class ThreeDExample(ThreeDSlide):
            def construct(self):
                title = Text("A 2D Text")

                self.play(FadeIn(title))
                self.next_slide()

                sphere = Sphere([0, 0, -3])

                self.move_camera(phi=PI/3, theta=-PI/4, distance=7)
                self.play(
                    GrowFromCenter(sphere),
                    Transform(title, Text("A 3D Text"))
                )
                self.next_slide()

                bye = Text("Bye!")

                self.next_slide(loop=True)
                self.wipe(
                    self.mobjects_without_canvas,
                    [bye],
                    direction=UP
                )
                self.wait(.5)
                self.wipe(
                    self.mobjects_without_canvas,
                    [title, sphere],
                    direction=DOWN
                )
                self.wait(.5)
                self.next_slide()

                self.play(*[FadeOut(mobject) for mobject in self.mobjects])

    """

    pass
