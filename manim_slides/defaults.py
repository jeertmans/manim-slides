import platform

FOLDER_PATH: str = "./slides"
CONFIG_PATH: str = ".manim-slides.json"

if platform.system() == "Windows":
    RIGHT_ARROW_KEY_CODE = 2555904
    LEFT_ARROW_KEY_CODE = 2424832
else:
    RIGHT_ARROW_KEY_CODE = 65363
    LEFT_ARROW_KEY_CODE = 65361
