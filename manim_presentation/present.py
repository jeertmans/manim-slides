import cv2
import numpy as np
import os
import sys
import json
import math
import time
import argparse
from enum import Enum

class Config:
    QUIT_KEY = ord("q")
    CONTINUE_KEY = 83      #right arrow
    BACK_KEY = 81          #left arrow
    REWIND_KEY = ord("r")
    PLAYPAUSE_KEY = 32     #spacebar

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
    def __init__(self, config):
        self.slides = config["slides"]
        self.files = config["files"]

        self.reset()        
        self.load_files()
        self.add_last_slide()
    
    def reset(self):
        self.current_animation = 0
        self.current_slide_i = 0


    def add_last_slide(self):
        last_slide_end = self.slides[-1]["end_animation"]
        last_animation = len(self.files) - 1
        self.slides.append(dict(
            start_animation = last_slide_end,
            end_animation = last_animation,
            type = "last",
            number = len(self.slides) + 1
        ))
    
    def load_files(self):
        self.caps = list()
        for f in self.files:
            self.caps.append(cv2.VideoCapture(f))

    def next(self):
        self.current_slide_i += 1
        self.current_animation = self.current_slide["start_animation"]
    
    def prev(self):
        self.current_slide_i = max(0, self.current_slide_i - 1)
        self.current_animation = self.current_slide["start_animation"]

    def rewind(self):
        self.current_animation = self.current_slide["start_animation"]

    @property
    def current_slide(self):
        return self.slides[self.current_slide_i]
    
    @property
    def current_cap(self):
        return self.caps[self.current_animation]

    @property
    def fps(self):
        return self.current_cap.get(cv2.CAP_PROP_FPS)

    def get_frame_and_state(self):
        ret, frame = self.current_cap.read()
        state = State.PLAYING
        if ret:
            self.lastframe = frame
        else:
            self.current_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            if self.current_slide["end_animation"] == self.current_animation + 1:
                if self.current_slide["type"] == "slide":
                    state = State.WAIT
                elif self.current_slide["type"] == "loop":
                    self.current_animation = self.current_slide["start_animation"]
                elif self.current_slide["type"] == "last":
                    return self.lastframe, State.END
            elif self.current_slide["type"] == "last" and self.current_slide["end_animation"] == self.current_animation:
                return self.lastframe, State.END
            else:
                self.current_animation += 1
            
        return self.lastframe, state


class Display:
    def __init__(self, presentations, start_paused=False):
        self.presentations = presentations
        self.start_paused = start_paused

        self.state = State.PLAYING
        self.lastframe = None
        self.current_presentation_i = 0
        self.last_time = now()
    
    @property
    def current_presentation(self):
        return self.presentations[self.current_presentation_i]
    
    def run(self):
        while True:
            if self.state == State.PLAYING:
                self.lastframe, self.state = self.current_presentation.get_frame_and_state()
                if self.start_paused:
                    self.state = State.PAUSED
                    self.start_paused = False
            if self.state == State.END:
                if self.current_presentation_i == len(self.presentations) - 1:
                    self.quit()
                else:
                    self.current_presentation_i += 1
                    self.state = State.PLAYING
                
            self.show_video()
            self.show_info()
            self.handle_key()
    
    def show_video(self):
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
        lag = now() - self.last_time
        self.last_time = now()
        key = cv2.waitKey(fix_time(sleep_time - lag)) & 0xFF

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
            self.current_presentation.rewind()
            self.state = State.PLAYING

    
    def quit(self):
        cv2.destroyAllWindows()
        sys.exit()


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("scenes", metavar="scenes", type=str, nargs="+", help="Scenes to present")
    parser.add_argument("--folder", type=str, default="./presentation", help="Presentation files folder")
    parser.add_argument("--start-paused", action="store_true", help="Start paused")
    

    args = parser.parse_args()

    presentations = list()
    for scene in args.scenes:
        config_file = os.path.join(args.folder, f"{scene}.json")
        if not os.path.exists(config_file):
            raise Exception(f"File {config_file} does not exist, check the scene name and make sure to use Slide as your scene base class")
        config = json.load(open(config_file))
        presentations.append(Presentation(config))

    display = Display(presentations, start_paused=args.start_paused)
    display.run()

if __name__ == "__main__":
    main()