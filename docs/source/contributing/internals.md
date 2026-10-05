# Internals

Manim-Slides' work is split in two steps: first, when rendering animation, and, second, when converting multiple animations into one slides presentation.

## Rendering

To render animations, Manim Slides simply uses Manim or ManimGL, and creates some additional output files that it needs for the presentation.

### Segmented video reversal

Long animations are split into segments and reversed by spawned worker processes.
Fresh interpreters avoid inheriting locks from renderer or logging threads.
Direct calls to `reverse_video_file` from a script need an
`if __name__ == "__main__":` guard, as with other multiprocessing code.

The controlled reproducer for the inherited-lock failure is a three-second slide
on platforms with `fork`:

```sh
uv run manim render tests/data/reversal_deadlock.py ReversalDeadlock -ql --disable_caching
```

It selects `fork` as the application's default and synchronizes a background
thread so that it holds the renderer's Rich console lock when workers fork.
PyAV logging in an inherited worker then waits on a lock whose owner thread no
longer exists. Spawned reversal workers finish even with that application default.
This forces a concrete unsafe-fork condition; it does not establish that every
stall reported in issues #562 and #569 has this same cause.

The utility regression runs the same setup on a tiny generated video with one
and two workers, checks every reversed frame, and kills the entire subprocess
group after 30 seconds if reversal stalls:

```sh
uv run pytest tests/test_utils.py -k inherited_renderer_lock
```

The controlled fork test is skipped on platforms without `fork`. The frame-order
test exercises real spawned workers on all supported platforms. When comparing
against the old default-context pool, run the regression above to bound the
stall and clean up its workers; the standalone scene deliberately has no timeout.

## Slides presentation

Manim Slides searches for the local artifacts it generated previously, and concatenates them into one presentation. For the graphical interface, it uses `PySide6`.
