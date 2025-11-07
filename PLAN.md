# Subsection Support Plan

Goal: introduce `Slide.next_subsection()` so authors can mark intra-slide pause points that (1) enhance interactive presenters (Qt, RevealJS) and (2) optionally drive PDF/PPTX export, while leaving existing slide behavior untouched by default.

## 1. Authoring & Data Model
- Add `Slide.next_subsection(name: str | None = None, *, auto_next: bool = False)` in `manim_slides/slide/manim.py`.
  - Simply records metadata; no calls to `Scene.next_section`, no state reset.
  - Store subsection markers (animation index + optional label/auto flag) in a small buffer on `BaseSlide`.
- Extend `PreSlideConfig` and `BaseSlideConfig` to carry an immutable tuple of `SubsectionMarker` objects. When `next_slide()` finalizes a slide, it copies the buffered markers into the `PreSlideConfig` and clears the buffer. `_add_last_slide()` must perform the same transfer so the trailing slide collects its subsections.
- Ensure serialization/deserialization paths (CLI config loading, tests) accept the new field but default to empty tuples, preserving backward compatibility.

## 2. PDF Export (Beamer-style)
- Add CLI/config flag `--pdf-subsections` with values `none` (default), `final`, `all`.
  - `none`: exactly today’s behavior (one page per slide; first/last frame depending on `frame_index`).
  - `final`: if a slide recorded subsections, render the last subsection’s frame for that slide’s single PDF page (still one page per slide).
  - `all`: emit extra PDF pages per subsection (first/last frame per subsection, based on `frame_index`), keeping the slide’s own page as well.
- Implement by teaching `PDF.convert_to` to inspect `slide_config.subsections`; reuse `read_image_from_video_file` with explicit frame indices or timestamps derived from the cached animations.
- Update `docs/source/reference/sharing.md` to explain the new flag and clarify that `next_subsection` affects PDFs only when explicitly requested.

## 3. RevealJS / HTML Presenter
- When building the HTML config, propagate subsection metadata so each slide’s `<video>` gets `data-manim-subsections="[t1,t2,...]"` plus optional labels.
- Inject a lightweight script into `templates/revealjs.html`:
  - Converts subsections into Reveal fragments; each fragment seek-pause sequence uses `video.currentTime = subsection.time; video.pause();`.
  - Keyboard navigation: advancing fragments walks through subsections before switching slides. Provide a CLI toggle `--html-subsections` (default `disabled`) to gate this behavior.
- PDF-from-HTML (Reveal’s own printing) should treat subsections like fragments when `pdfSeparateFragments` is true, matching existing semantics.

## 4. Qt Presenter (`manim-slides present`)
- Extend slide loading (`manim_slides/present/player.py`) to read subsection cue points.
- Navigation rules:
  - Right/space advance to the next subsection; only when the last subsection is reached does the slide advance.
  - Left arrow steps backward through subsections, then to the previous slide.
  - Provide config flag `--present-subsections=off|pause|autoplay` (default `off`). `pause` pauses playback at each marker until the presenter resumes; `autoplay` merely shows markers on the scrubber.
- UI: show a small overlay of dots/progress bar segments representing subsections; highlight the current one.

## 5. PowerPoint Export (Temporary Workaround)
- When `--pptx-subsections=split` is enabled (default `off`), duplicate each slide per subsection:
  - Split the base MP4 into fragments using existing cached frame ranges; store them in a temp dir without recompressing when possible.
  - Create an extra PPTX slide for each fragment, embedding only that trimmed clip and an appropriate poster frame (first frame of the fragment). Maintain the original slide numbering by appending letters (e.g., 3a, 3b) in the notes/title for clarity.
  - If subsections are disabled or the flag is `off`, fall back to today’s single-slide-per-video behavior.
- Document this as a temporary solution until cue-point based playback is available.

## 6. Testing & Documentation
- Unit tests:
  - `tests/test_slide.py`: ensure `next_subsection` buffers markers, does not change `_current_slide`, and survives `skip_animations`.
  - `tests/test_convert.py`: add PDF and PPTX fixtures covering all new flags.
  - `tests/test_present.py`/Qt mocks: verify navigation logic honors subsections.
- Docs:
  - New “Subsections” page in `docs/source/reference` covering author workflow, CLI flags, and behavior per output format.
  - Changelog entries summarizing PDF options, presenter pause behavior, and PPTX splitting.

## 7. Rollout & Backward Compatibility
- Default flags keep new functionality disabled so existing projects render identically.
- Provide migration notes: authors can sprinkle `next_subsection()` today without changing outputs; they only opt in per backend via CLI/config switches.
- Gather feedback before making subsections default in presenters, ensuring performance (seek latency) is acceptable on large videos.
