from manim import (
    BLUE,
    DOWN,
    RED,
    Circle,
    Create,
    FadeIn,
    Square,
    Text,
    Write,
)
from PIL import Image, ImageDraw, ImageFont

from manim_slides.slide.manim import Slide


class StaticImageExample(Slide):
    def construct(self) -> None:
        # Create some static images for demonstration
        def create_sample_image(text: str, filename: str) -> str:
            # Create a simple image with text
            img = Image.new("RGB", (800, 600), color="white")
            draw = ImageDraw.Draw(img)

            try:
                font = ImageFont.truetype("arial.ttf", 40)
            except OSError:
                font = ImageFont.load_default()

            # Add text to the image
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            x = (800 - text_width) // 2
            y = (600 - text_height) // 2

            draw.text((x, y), text, fill="black", font=font)

            # Save the image
            img.save(filename)
            return filename

        # Create sample images
        image1_path = create_sample_image("Static Image Slide 1", "static_image1.png")
        image2_path = create_sample_image("Static Image Slide 2", "static_image2.png")

        # First slide with animation
        title = Text("Static Image Support", font_size=48)
        subtitle = Text(
            "Manim Slides now supports static images!", font_size=24
        ).next_to(title, DOWN)

        self.play(FadeIn(title))
        self.play(FadeIn(subtitle))

        # Second slide with static image
        self.next_slide(static_image=image1_path)

        # Third slide with animation again
        self.next_slide()
        circle = Circle(radius=2, color=BLUE)
        square = Square(side_length=3, color=RED)

        self.play(Create(circle))
        self.play(Create(square))

        # Fourth slide with another static image (different content)
        self.next_slide(static_image=image2_path)

        # Final slide
        self.next_slide()
        final_text = Text(
            "Static images work seamlessly with animations!", font_size=36
        )
        self.play(Write(final_text))
