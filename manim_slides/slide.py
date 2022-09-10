import json
import os
import platform
import shutil
import subprocess

from tqdm import tqdm

from .defaults import FOLDER_PATH
from .manim import FFMPEG_BIN, MANIMGL, Scene, ThreeDScene, config, logger


def reverse_video_path(src: str) -> str:
    file, ext = os.path.splitext(src)
    return f"{file}_reversed{ext}"


def reverse_video_file(src: str, dst: str):
    command = [FFMPEG_BIN, "-i", src, "-vf", "reverse", dst]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process.communicate()


class Slide(Scene):
    def __init__(self, *args, output_folder=FOLDER_PATH, **kwargs):
        if MANIMGL:
            if not os.path.isdir("videos"):
                os.mkdir("videos")
            kwargs["file_writer_config"] = {
                "break_into_partial_movies": True,
                "output_directory": "",
                "write_to_movie": True,
            }

            kwargs["preview"] = False

        super().__init__(*args, **kwargs)

        self.output_folder = output_folder
        self.slides = list()
        self.current_slide = 1
        self.current_animation = 0
        self.loop_start_animation = None
        self.pause_start_animation = 0

    @property
    def partial_movie_files(self):
        if MANIMGL:
            from manimlib.utils.file_ops import get_sorted_integer_files

            kwargs = {
                "remove_non_integer_files": True,
                "extension": self.file_writer.movie_file_extension,
            }
            return get_sorted_integer_files(
                self.file_writer.partial_movie_directory, **kwargs
            )
        else:
            return self.renderer.file_writer.partial_movie_files

    @property
    def show_progress_bar(self):
        if MANIMGL:
            return getattr(super(Scene, self), "show_progress_bar", True)
        else:
            return config["progress_bar"] != "none"

    @property
    def leave_progress_bar(self):
        if MANIMGL:
            return getattr(super(Scene, self), "leave_progress_bars", False)
        else:
            return config["progress_bar"] == "leave"

    def play(self, *args, **kwargs):
        super().play(*args, **kwargs)
        self.current_animation += 1

    def pause(self):
        self.slides.append(
            dict(
                type="slide",
                start_animation=self.pause_start_animation,
                end_animation=self.current_animation,
                number=self.current_slide,
            )
        )
        self.current_slide += 1
        self.pause_start_animation = self.current_animation

    def start_loop(self):
        assert self.loop_start_animation is None, "You cannot nest loops"
        self.loop_start_animation = self.current_animation

    def end_loop(self):
        assert (
            self.loop_start_animation is not None
        ), "You have to start a loop before ending it"
        self.slides.append(
            dict(
                type="loop",
                start_animation=self.loop_start_animation,
                end_animation=self.current_animation,
                number=self.current_slide,
            )
        )
        self.current_slide += 1
        self.loop_start_animation = None
        self.pause_start_animation = self.current_animation

    def save_slides(self, use_cache=True):

        if not os.path.exists(self.output_folder):
            os.mkdir(self.output_folder)

        files_folder = os.path.join(self.output_folder, "files")
        if not os.path.exists(files_folder):
            os.mkdir(files_folder)

        scene_name = type(self).__name__
        scene_files_folder = os.path.join(files_folder, scene_name)

        old_animation_files = set()

        if not os.path.exists(scene_files_folder):
            os.mkdir(scene_files_folder)
        elif not use_cache:
            shutil.rmtree(scene_files_folder)
            os.mkdir(scene_files_folder)
        else:
            old_animation_files.update(os.listdir(scene_files_folder))

        files = list()
        for src_file in tqdm(
            self.partial_movie_files,
            desc=f"Copying animation files to '{scene_files_folder}' and generating reversed animations",
            leave=self.leave_progress_bar,
            ascii=True if platform.system() == "Windows" else None,
            disable=not self.show_progress_bar,
        ):
            filename = os.path.basename(src_file)
            _hash, ext = os.path.splitext(filename)

            rev_filename = f"{_hash}_reversed{ext}"

            dst_file = os.path.join(scene_files_folder, filename)
            # We only copy animation if it was not present
            if filename in old_animation_files:
                old_animation_files.remove(filename)
            else:
                shutil.copyfile(src_file, dst_file)

            # We only reverse video if it was not present
            if rev_filename in old_animation_files:
                old_animation_files.remove(rev_filename)
            else:
                rev_file = os.path.join(scene_files_folder, rev_filename)
                reverse_video_file(src_file, rev_file)

            files.append(dst_file)

        logger.info(
            f"Copied {len(files)} animations to '{os.path.abspath(scene_files_folder)}' and generated reversed animations"
        )

        slide_path = os.path.join(self.output_folder, "%s.json" % (scene_name,))

        f = open(slide_path, "w")
        json.dump(dict(slides=self.slides, files=files), f)
        f.close()
        logger.info(
            f"Slide '{scene_name}' configuration written in '{os.path.abspath(slide_path)}'"
        )

    def run(self, *args, **kwargs):
        """MANIMGL renderer"""
        super().run(*args, **kwargs)
        self.save_slides(use_cache=False)

    def render(self, *args, **kwargs):
        """MANIM render"""
        # We need to disable the caching limit since we rely on intermidiate files
        max_files_cached = config["max_files_cached"]
        config["max_files_cached"] = float("inf")

        super().render(*args, **kwargs)

        config["max_files_cached"] = max_files_cached

        self.save_slides()


class ThreeDSlide(Slide, ThreeDScene):
    pass
