# Performance Tips for Large Presentations

Rendering large `manim-slides` presentations can slow if you are not careful.
This page collects practical tips for cutting render times, especially during
development.

---

## Table of Contents

1. [Render at Low Quality During Development](#render-at-low-quality-during-development)
2. [Keep Scenes Small and Self-Contained](#keep-scenes-small-and-self-contained)
3. [Render Only the Animations You Need](#render-only-the-animations-you-need)
4. [Parallelize Rendering Across Scenes](#parallelize-rendering-across-scenes)
5. [Reverse-Animation](#reverse-animation)
6. [Minimize TeX Calls](#minimize-tex-calls)

---
## Render at Low Quality During Development

The biggest time-saver is to stop rendering at full quality while you are
still iterating.

Use the `-ql` flag (low quality) and, optionally, drop the frame rate while you
are working:

```bash
manim-slides render your_script.py YourClass -ql --fps=10
```

Only switch back to high quality (`-qh`) or full-HD (`-qk`) once the
presentation content and timing are finalized.

---

## Keep Scenes Small and Self-Contained

A presentation made up of a single `construct()` method is hard to debug and
forces a full re-render every time anything changes.  The most effective
structure for large presentations is to split each logical section into its own
`Slide` subclass:

```python
from manim import *
from manim_slides import Slide


class Introduction(Slide):
    def construct(self):
        ...


class ExplainConcepts(Slide):
    def construct(self):
        ...


class ShowResults(Slide):
    def construct(self):
        ...
```

Each class can now be rendered independently from the command line.  When you are
happy with every scene, stitch them together into a single presentation with
`manim-slides convert`:

```bash
manim-slides convert --to html \
    Introduction ExplainConcepts ShowResults \
    presentation_output.html
```

> **Note**: You may find it useful to create a bash file for the above command
> to avoid remembering it, especially when the number of scenes becomes large.

---
## Render Only the Animations You Need

Even when you are working on a single scene, there is no reason to re-render
everything.  `manim-slides` lets you target a contiguous range of animations with the
`-n` flag:

```bash
manim-slides render your_file.py YourClass -n a,b
```

Here `a` is the index of the first animation to render and `b` is the last (both
inclusive).  This is especially useful when a bug or layout issue is isolated to
one section — you can re-render just those slides and skip the rest.

---


## Parallelize Rendering Across Scenes

Because each scene is independent, you can render multiple scenes at the same
time — one per CPU core.  There is one important caveat: generated artifacts such
as TeX images will collide if every scene writes to the same directory.  Give
each scene its own `media_dir` to avoid this. A sample render script is below
that automatically creates media directories based upon the scene name.

<details>

<summary>A sample parallelized render script.</summary>

```python
## Usage
## python fast-render.py <file_name> <flags>
## i.e. python fast-render.py file-name.py -q m

import sys
import os
import ast
import subprocess
from multiprocessing import Pool, cpu_count

FAILED_SCENES = []


def find_scene_classes(file_path):
    """
    Parses the python file using AST to find all classes that likely
    inherit from a Manim Scene (heuristic: base class name contains 'Scene').
    """
    with open(file_path, "r") as source:
        tree = ast.parse(source.read())

    scene_names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for base in node.bases:
                # Check if it inherits from something that looks like a Scene
                # e.g., Scene, MovingCameraScene, ThreeDScene
                base_name = ""
                if isinstance(base, ast.Name):
                    base_name = base.id
                elif isinstance(base, ast.Attribute):
                    base_name = base.attr

                if "Scene" in base_name or "Slide" in base_name:
                    scene_names.append(node.name)
                    break
    return scene_names


def render_worker(args):
    """
    Worker function to execute the manim command.
    """
    cmd, scene_name = args
    print(f"Starting render: {scene_name}...")
    print(f"Command is {cmd}")
    try:
        result = subprocess.run(
            cmd, shell=True, check=True, text=True, stdout=subprocess.DEVNULL)
        if result.returncode == 0:
            print(f"Finished: {scene_name}")
        else:
            print(f"Error in {scene_name}:\n{result.stderr}")
            FAILED_SCENES.append(scene_name)
    except Exception as e:
        print(f"Failed: {scene_name} with exception {e}")
        FAILED_SCENES.append(scene_name)


def main():
    if len(sys.argv) < 2:
        print("Usage: python fast_render.py <your_script.py> [flags]")
        print("Example: python fast_render.py animation.py -ql")
        return

    target_file = sys.argv[1]

    # Pass any extra flags (like -ql or -pk) provided by the user
    extra_flags = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""

    if not os.path.exists(target_file):
        print(f"Error: File '{target_file}' not found.")
        return

    print(f"Scanning '{target_file}' for scenes...")
    scenes = find_scene_classes(target_file)

    if not scenes:
        print("No classes inheriting from 'Scene' or 'Slide' found.")
        return

    print(f"Found {len(scenes)} scenes: {', '.join(scenes)}")

    # Prepare commands
    # Format: manim-slides render <flags> <filename> <SceneName>
    tasks = []
    for scene in scenes:
        command = f"manim-slides render --media_dir media_{scene} {extra_flags} {target_file} {scene}"
        tasks.append((command, scene))

    # Use roughly 75% of available CPU cores to prevent system freeze
    # Adjust this if your machine starts running out of memory
    workers = max(1, int(cpu_count() * 0.75))
    print(f"Rendering with {workers} parallel processes...\n")

    with Pool(processes=workers) as pool:
        pool.map(render_worker, tasks)
        pool.close()
        pool.join()

    print("\nAll render jobs completed.")

    if len(FAILED_SCENES):
        print(f"The following {len(FAILED_SCENES)} scenes had errors: {FAILED_SCENES}.")
    else:
        print("All render jobs were successful!")


if __name__ == "__main__":
    main()
```

</details>

With isolated media directories you can safely fan out rendering across as many
threads or processes as you have cores; however, you may wish to limit to fewer
than maximum to reduce parallel RAM usage.  After all jobs finish, run your
`manim-slides convert` command as usual to assemble the final presentation.

> **Tip:** Before doing a final production render, delete all `media_*` folders
> and the `slides/` folder first.  This ensures no silently failed or stale
> artifacts are included in the final output.

---

## Reverse-Animation By default, Manim Slides generates a reversed copy of
every slide so that you can navigate backwards during a live presentation.  For
output formats that do not use reversed animations, such as PPTX or HTML, this
step can be safely turned off to reduce rendering time.

Set the class attribute `skip_reversing = True` to turn it off:


```python
from manim import *
from manim_slides import Slide


class Presentation(Slide):
    skip_reversing = True

    def construct(self):
        self.play(...)
```

When reversed slides *are* enabled their generation can sometimes hang
indefinitely.  The root cause is an internal parallelization step that is prone
to deadlocking.  A known workaround is to disable that parallelization by setting
`max_duration_before_split_reverse` to `None`:

```python
class Presentation(Slide):
    max_duration_before_split_reverse = None

    def construct(self):
        ...
```

---

## Minimize TeX Calls

`Tex` and `MathTex` objects are slow to create as each
one requires LaTeX compilation.  In a large presentation, these
calls add up quickly.  `Tex` does produce noticeably better kerning
than `Text` for many strings, even when no maths is involved, so a potential
strategy is to iterate using `Text` and switch to `Tex` when you are ready to
render the final presentation.

```python
class Presentation(Slide):
    def construct(self):
        # change this to Tex at final render
        TextMobject = Text
        text = TextMobject(
            "Hello! This will be text for iteration, and can switch to TeX for better kerning at the end!"
        )
```
