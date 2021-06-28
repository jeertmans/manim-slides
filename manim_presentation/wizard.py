import cv2
import numpy as np
import json
import os
import sys

def prompt(question):
    font_args = (cv2.FONT_HERSHEY_SIMPLEX, 0.7, 255)
    display = np.zeros((130, 420), np.uint8)
    
    cv2.putText(
        display,
        "* Manim Presentation Wizard *",
        (50, 33),
        *font_args
    )
    cv2.putText(
        display,
        question,
        (30, 85),
        *font_args
    )

    cv2.imshow("wizard", display)
    return cv2.waitKeyEx(-1)

def main():
    if(os.path.exists("./manim-presentation.json")):
        print("The manim-presentation.json configuration file exists")
        ans = input("Do you want to continue and overwrite it? (y/n): ")
        if ans != "y": sys.exit(0)

    prompt("Press any key to continue")
    PLAYPAUSE_KEY = prompt("Press the PLAY/PAUSE key")
    CONTINUE_KEY = prompt("Press the CONTINUE/NEXT key")
    BACK_KEY = prompt("Press the BACK key")
    REWIND_KEY = prompt("Press the REWIND key")
    QUIT_KEY = prompt("Press the QUIT key")
    
    config_file = open("./manim-presentation.json", "w")
    json.dump(dict(
        PLAYPAUSE_KEY=PLAYPAUSE_KEY,
        CONTINUE_KEY=CONTINUE_KEY,
        BACK_KEY=BACK_KEY,
        REWIND_KEY=REWIND_KEY,
        QUIT_KEY=QUIT_KEY
    ), config_file)
    config_file.close()

    
    