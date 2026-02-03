# Performance Tips for Large Presentations

Rendering long Manim Slides presentations can be slow if you are not careful.
This page collects practical tips for cutting render times, especially during
development.

:::{info}
If you know other tips and would like to share them,
do not hesitate to contribute to this page!
*(See the little pen icon at the top of this page.)*
:::

## Table of Contents

1. [Render at Low Quality During Development](#render-at-low-quality-during-development)
2. [Keep Scenes Small and Self-Contained](#keep-scenes-small-and-self-contained)
3. [Render Only the Animations You Need](#render-only-the-animations-you-need)
4. [Parallelize Rendering Across Scenes](#parallelize-rendering-across-scenes)
5. [Disable Reverse-Animation](#disable-reverse-animation)
6. [Minimize TeX Calls](#minimize-tex-calls)

## Render at Low Quality During Development

The biggest time-saver is to stop rendering at full quality while you are
still iterating.

Use the `-ql` flag (low quality) and, optionally, drop the frame rate while you
are working on your animations:

```bash
manim-slides render your_script.py YourClass -ql --fps=10
```

Only switch back to a higher quality (e.g., `-qh` for full HD or `-qk` for
4K)  once the presentation content and timing are finalized.

## Keep Scenes Small and Self-Contained

A presentation made up of a single `construct()` method is hard to debug and
forces a full re-render every time anything changes[^1].  The most effective
structure for large presentations is to split each logical section into its own
`Slide` subclass:

[^1]: Although Manim (especially the community edition) provides a caching
  mechanism to avoid re-rendering all the slides, modifying a slide can quickly
  cause a cascade effect in all subsequent files, rendering the caching system
  ineffective.
  To avoid this, try breaking your slides into independent animations.

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

Each class can now be rendered independently from the command line. When you
are happy with every scene, stitch them together into a single presentation
with `manim-slides convert`:

```bash
manim-slides convert --to html \
    Introduction ExplainConcepts ShowResults \
    presentation_output.html
```

:::{note}
 You may find it useful to create a bash file for the above command
to avoid remembering it, especially when the number of scenes becomes large.
:::

## Render Only the Animations You Need

Even when you are working on a single scene, there is no reason to re-render
everything. Manim (and Manim Slides by extension) lets you target a contiguous
range of animations with the `-n` flag:

```bash
manim-slides render your_file.py YourClass -n a,b
```

Here, a is the index of the first animation to render, and b is the index
of the last animation to render (both inclusive). You can omit the start
or end indices to render either from the first animation or until the last
animation, respectively.
This is especially useful when a bug or layout issue is isolated to one section.
You can re-render just those slides and skip the rest.

## Parallelize Rendering Across Scenes

:::{important}
Parallel rendering is (currently) not a feature provided by Manim Slides,
but rather an improvement suggested by
[@jdgsmallwood](https://github.com/jdgsmallwood).

If you wish to see this better integrated into Manim Slides, please
raise an issue on GitHub!
:::

Because each scene is independent, you can render multiple scenes at the same
time; e.g., one per CPU thread. There is one important caveat:
generated artifacts such as TeX images will collide if every scene writes to
the same directory. To fix this, give each scene its own `media_dir` to
file collision. Below, we provide a sample render script is that
automatically creates media directories based upon the scene name.

<details>

<summary>A sample parallelized render script.</summary>

<!-- TODO: we should expose Manim Slides' logger to avoid using print statements everywhere -->

:::{warning}
The script below is provided as is, and may or may not work,
depending on your application case.

For any issue, please report them on GitHub.
:::

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
        command = (
            f"manim-slides render --media_dir media_{scene} "
            f"{extra_flags} {target_file} {scene}"
        )
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

:::{tip}
Before doing a final production render, delete all `media_*` folders
and the `slides/` folder first.  This ensures no silently failed or stale
artifacts are included in the final output.
:::

## Disable Reverse-Animation

By default, Manim Slides generates a reversed copy of every slide so that you
can navigate backwards during a live presentation. For output formats that do
not use reversed animations, such as PPTX or HTML, this step can be safely
turned off to reduce rendering time.

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
indefinitely
(see [#562](https://github.com/jeertmans/manim-slides/issues/562)).
The root cause is an internal parallelization step that is prone
to deadlocking.  A known workaround is to disable that parallelization by
setting `max_duration_before_split_reverse` to `None`:

```python
class Presentation(Slide):
    max_duration_before_split_reverse = None

    def construct(self):
        ...
```

## Minimize TeX Calls

`Tex` and `MathTex` objects are slow to create as each one requires LaTeX
compilation.  In a large presentation, these calls add up quickly. However,
LaTeX produce noticeably better kerning than `Text` for many strings, even
when no math is involved. So, a potential strategy is to first iterate using
`Text`, and switch to back `Tex` when you are ready to render the final
presentation. Note that you will probably need to adapt the font size between
the two.

```python
class Presentation(Slide):
    def construct(self):
        # change this to Tex at final render
        TextMobject = Text
        text = TextMobject(
            "Hello! This will be text initially."
            "Switch to TeX at the end for better kerning!"
        )
```
