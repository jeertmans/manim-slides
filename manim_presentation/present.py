import cv2
import numpy as np
import os
import sys
import json
import math
import time
import argparse
from enum import Enum
import platform

class Config:
    @classmethod
    def init(cls):
        if platform.system() == "Windows":
            cls.QUIT_KEY = ord("q")
            cls.CONTINUE_KEY = 2555904     #right arrow
            cls.BACK_KEY = 2424832         #left arrow
            cls.REWIND_KEY = ord("r")
            cls.PLAYPAUSE_KEY = 32         #spacebar
        else:
            cls.QUIT_KEY = ord("q")
            cls.CONTINUE_KEY = 65363       #right arrow
            cls.BACK_KEY = 65361           #left arrow
            cls.REWIND_KEY = ord("r")
            cls.PLAYPAUSE_KEY = 32         #spacebar
        
        if os.path.exists(os.path.join(os.getcwd(), "./manim-presentation.json")):
            json_config = json.load(open(os.path.join(os.getcwd(), "./manim-presentation.json"), "r"))
            for key, value in json_config.items():
                setattr(cls, key, value)

class State(Enum):
    PLAYING = 0
    PAUSED = 1
    WAIT = 2
    END = 3

    def __str__(self):
        if self.value == 0: return "Playing"
        if self.value == 1: return "Paused"
        if self.value == 2: return "Wait"
        if self.value == 3: return "End"
        return "..."

def now():
    return round(time.time() * 1000)

def fix_time(x):
    return x if x > 0 else 1

class Presentation:
    def __init__(self, config, last_frame_next=False):
        self.last_frame_next = last_frame_next
        self.slides = config["slides"]
        self.files = config["files"]

        self.lastframe = []

        self.reset()        
        self.load_files()
        self.add_last_slide()

    def add_last_slide(self):
        last_slide_end = self.slides[-1]["end_animation"]
        last_animation = len(self.files)
        self.slides.append(dict(
            start_animation = last_slide_end,
            end_animation = last_animation,
            type = "last",
            number = len(self.slides) + 1,
            terminated = False
        ))



    def reset(self):
        self.current_animation = 0
        self.current_slide_i = 0
        self.slides[-1]["terminated"] = False
    
    def load_files(self):
        self.caps = list()
        for f in self.files:
            self.caps.append(cv2.VideoCapture(f))

    def next(self):
        if self.current_slide["type"] == "last":
            self.current_slide["terminated"] = True
        else:
            self.current_slide_i = min(len(self.slides) - 1, self.current_slide_i + 1)
            self.rewind_slide()
    
    def prev(self):
        self.current_slide_i = max(0, self.current_slide_i - 1)
        self.rewind_slide()

    def rewind_slide(self):
        self.current_animation = self.current_slide["start_animation"]
        self.current_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    @property
    def current_slide(self):
        return self.slides[self.current_slide_i]
    
    @property
    def current_cap(self):
        return self.caps[self.current_animation]

    @property
    def fps(self):
        return self.current_cap.get(cv2.CAP_PROP_FPS)

    # This function updates the state given the previous state.
    # It does this by reading the video information and checking if the state is still correct.
    # It returns the frame to show (lastframe) and the new state.
    def update_state(self, state):
        if state == State.PAUSED:
            if len(self.lastframe) == 0:
                _, self.lastframe = self.current_cap.read()
            return self.lastframe, state
        still_playing, frame = self.current_cap.read()
        if still_playing:
            self.lastframe = frame
        elif state in [state.WAIT, state.PAUSED]:
            return self.lastframe, state
        elif self.current_slide["type"] == "last" and self.current_slide["terminated"]:
            return self.lastframe, State.END

        if not still_playing:
            if self.current_slide["end_animation"] == self.current_animation + 1:
                if self.current_slide["type"] == "slide":
                    # To fix "it always ends one frame before the animation", uncomment this.
                    # But then clears on the next slide will clear the stationary after this slide.
                    if self.last_frame_next:
                        self.next_cap = self.caps[self.current_animation + 1]
                        self.next_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        _, self.lastframe = self.next_cap.read()
                    state = State.WAIT
                elif self.current_slide["type"] == "loop":
                    self.current_animation = self.current_slide["start_animation"]
                    state = State.PLAYING
                    self.rewind_slide()
                elif self.current_slide["type"] == "last":
                    self.current_slide["terminated"] = True
            elif self.current_slide["type"] == "last" and self.current_slide["end_animation"] == self.current_animation:
                state = State.WAIT
            else:
                # Play next video!
                self.current_animation += 1
                # Reset video to position zero if it has been played before
                self.current_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            
        return self.lastframe, state


class Display:
    def __init__(self, presentations, start_paused=False, fullscreen=False):
        self.presentations = presentations
        self.start_paused = start_paused

        self.state = State.PLAYING
        self.lastframe = None
        self.current_presentation_i = 0

        self.lag = 0
        self.last_time = now()

        if fullscreen:
            cv2.namedWindow("Video", cv2.WND_PROP_FULLSCREEN)
            cv2.setWindowProperty("Video", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    
    @property
    def current_presentation(self):
        return self.presentations[self.current_presentation_i]
    
    def run(self):
        while True:
            self.lastframe, self.state = self.current_presentation.update_state(self.state)
            if self.state == State.PLAYING or self.state == State.PAUSED:
                if self.start_paused:
                    self.state = State.PAUSED
                    self.start_paused = False
            if self.state == State.END:
                if self.current_presentation_i == len(self.presentations) - 1:
                    self.quit()
                else:
                    self.current_presentation_i += 1
                    self.state = State.PLAYING
            self.handle_key()
            self.show_video()
            self.show_info()
    
    def show_video(self):
        self.lag = now() - self.last_time
        self.last_time = now()
        cv2.imshow("Video", self.lastframe) 

    def show_info(self):
        info = np.zeros((130, 420), np.uint8)
        font_args = (cv2.FONT_HERSHEY_SIMPLEX, 0.7, 255)
        grid_x = [30, 230]
        grid_y = [30, 70, 110]

        cv2.putText(
            info,
            f"Animation: {self.current_presentation.current_animation}",
            (grid_x[0], grid_y[0]),
            *font_args
        )
        cv2.putText(
            info,
            f"State: {self.state}",
            (grid_x[1], grid_y[0]),
            *font_args
        )

        cv2.putText(
            info,
            f"Slide {self.current_presentation.current_slide['number']}/{len(self.current_presentation.slides)}",
            (grid_x[0], grid_y[1]),
            *font_args
        )
        cv2.putText(
            info,
            f"Slide Type: {self.current_presentation.current_slide['type']}",
            (grid_x[1], grid_y[1]),
            *font_args
        )

        cv2.putText(
            info,
            f"Scene  {self.current_presentation_i + 1}/{len(self.presentations)}",
            ((grid_x[0]+grid_x[1])//2, grid_y[2]),
            *font_args
        )
        
        cv2.imshow("Info", info)
    
    def handle_key(self):
        sleep_time = math.ceil(1000/self.current_presentation.fps)
        key = cv2.waitKeyEx(fix_time(sleep_time - self.lag))
        
        if key == Config.QUIT_KEY:
            self.quit()
        elif self.state == State.PLAYING and key == Config.PLAYPAUSE_KEY:
            self.state = State.PAUSED
        elif self.state == State.PAUSED and key == Config.PLAYPAUSE_KEY:
            self.state = State.PLAYING
        elif self.state == State.WAIT and (key == Config.CONTINUE_KEY or key == Config.PLAYPAUSE_KEY):
            self.current_presentation.next()
            self.state = State.PLAYING
        elif self.state == State.PLAYING and key == Config.CONTINUE_KEY:
            self.current_presentation.next()
        elif key == Config.BACK_KEY:
            if self.current_presentation.current_slide_i == 0:
                self.current_presentation_i = max(0, self.current_presentation_i - 1)
                self.current_presentation.reset()
                self.state = State.PLAYING
            else:
                self.current_presentation.prev()
                self.state = State.PLAYING
        elif key == Config.REWIND_KEY:
            self.current_presentation.rewind_slide()
            self.state = State.PLAYING

    
    def quit(self):
        cv2.destroyAllWindows()
        sys.exit()


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("scenes", metavar="scenes", type=str, nargs="+", help="Scenes to present")
    parser.add_argument("--folder", type=str, default="./presentation", help="Presentation files folder")
    parser.add_argument("--start-paused", action="store_true", help="Start paused")
    parser.add_argument("--fullscreen", action="store_true", help="Fullscreen")
    parser.add_argument("--last-frame-next", action="store_true", help="Show the next animation first frame as last frame (hack)")
    
    args = parser.parse_args()
    args.folder = os.path.normcase(args.folder)

    Config.init()

    presentations = list()
    for scene in args.scenes:
        config_file = os.path.join(args.folder, f"{scene}.json")
        if not os.path.exists(config_file):
            raise Exception(f"File {config_file} does not exist, check the scene name and make sure to use Slide as your scene base class")
        config = json.load(open(config_file))
        presentations.append(Presentation(config, last_frame_next=args.last_frame_next))

    display = Display(presentations, start_paused=args.start_paused, fullscreen=args.fullscreen)
    display.run()

if __name__ == "__main__":
    main()
