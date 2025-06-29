from manim import *
from PIL import Image, ImageDraw, ImageFont

from manim_slides import Slide


class StaticImageExample(Slide):
    def construct(self):
        # Create a simple image programmatically
        img = Image.new("RGB", (800, 600), color="white")
        draw = ImageDraw.Draw(img)

        # Draw some text
        try:
            font = ImageFont.truetype("arial.ttf", 40)
        except:
            font = ImageFont.load_default()

        draw.text(
            (400, 300), "Static Image Slide", fill="black", anchor="mm", font=font
        )

        # Draw a simple shape
        draw.rectangle([200, 200, 600, 400], outline="blue", width=5)

        # Save the image
        img_path = "static_image.png"
        img.save(img_path)

        # First slide with animation
        title = Text("Static Image Support", font_size=48)
        subtitle = Text(
            "Manim Slides now supports static images!", font_size=24
        ).next_to(title, DOWN)

        self.play(FadeIn(title))
        self.play(FadeIn(subtitle))

        # Second slide with static image
        self.next_slide(static_image=img_path)

        # Third slide with animation again
        self.next_slide()
        circle = Circle(radius=2, color=BLUE)
        square = Square(side_length=3, color=RED)

        self.play(Create(circle))
        self.play(Create(square))

        # Fourth slide with another static image (different content)
        img2 = Image.new("RGB", (800, 600), color="lightblue")
        draw2 = ImageDraw.Draw(img2)
        draw2.text(
            (400, 300), "Another Static Image", fill="darkblue", anchor="mm", font=font
        )
        draw2.ellipse([250, 200, 550, 400], outline="red", width=5)

        img2_path = "static_image2.png"
        img2.save(img2_path)

        self.next_slide(static_image=img2_path)

        # Final slide
        self.next_slide()
        final_text = Text(
            "Static images work seamlessly with animations!", font_size=36
        )
        self.play(Write(final_text))
