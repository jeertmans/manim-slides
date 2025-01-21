# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!-- start changelog -->

(unreleased)=
## [Unreleased](https://github.com/jeertmans/manim-slides/compare/v5.4.0...HEAD)

(v5.4.0)=
## [v5.4.0](https://github.com/jeertmans/manim-slides/compare/v5.3.1...v5.4.0)

(v5.4.0-added)=
### Added

- Added `skip_animations` compatibility with ManimCE.
  [@Rapsssito](https://github.com/Rapsssito) [#516](https://github.com/jeertmans/manim-slides/pull/516)

(v5.4.0-chore)=
### Chore

- Bumped Manim to `>=0.19`, as it fixed OpenGL renderer issue.
  [#522](https://github.com/jeertmans/manim-slides/pull/522)

(v5.4.0-fixed)=
### Fixed

- Fixed OpenGL renderer having no partial movie files with Manim bindings.
  [#522](https://github.com/jeertmans/manim-slides/pull/522)
- Fixed `ConvertExample` example as `manim>=0.19` changed the `Code` class.
  [#522](https://github.com/jeertmans/manim-slides/pull/522)

(v5.3.1)=
## [v5.3.1](https://github.com/jeertmans/manim-slides/compare/v5.3.0...v5.3.1)

(v5.3.1-fixed)=
### Fixed

- Fixed HTML template to avoid missing slides when exporting with `--one-file`.
  [@Rapsssito](https://github.com/Rapsssito) [#515](https://github.com/jeertmans/manim-slides/pull/515)

(v5.3.0)=
## [v5.3.0](https://github.com/jeertmans/manim-slides/compare/v5.2.0...v5.3.0)

(v5.3.0-added)=
### Added

- Added CSS and JS inline for `manim-slides convert` if `--offline`
  and `--one-file` (`-cone_file`) are used for HTML output.
  [@Rapsssito](https://github.com/Rapsssito) [#505](https://github.com/jeertmans/manim-slides/pull/505)

(v5.3.0-changed)=
### Changed

- Deprecate `-cdata_uri` in favor of `-cone_file` for `manim-slides convert`.
  [@Rapsssito](https://github.com/Rapsssito) [#505](https://github.com/jeertmans/manim-slides/pull/505)
- Changed template to avoid micro-stuttering with `--one-file` in HTML presentation.
  [@Rapsssito](https://github.com/Rapsssito) [#508](https://github.com/jeertmans/manim-slides/pull/508)

(v5.2.0)=
## [v5.2.0](https://github.com/jeertmans/manim-slides/compare/v5.1.10...v5.2.0)

(v5.2.0-changed)=
### Changed

- The info window is now only shown in presentations when there
  are multiple monitors. However, the `--show-info-window` option
  was added to `manim-slides present` to force the info window.
  When there are multiple monitors, the info window will no longer
  be on the same monitor as the main window, unless overridden.
  [@PeculiarProgrammer](https://github.com/PeculiarProgrammer)
  [#482](https://github.com/jeertmans/manim-slides/pull/482)

(v5.2.0-chore)=
### Chore

- Bumped ManimGL to `>=1.7.1`, to remove conflicting dependencies
  with Manim's.
  [#499](https://github.com/jeertmans/manim-slides/pull/499)

- Bumped ManimGL to `>=1.7.2`, to remove `pyrr` from dependencies,
  and to avoid complex code for supporting both `1.7.1` and `>=1.7.2`,
  as the latter includes many breaking changes.
  [#506](https://github.com/jeertmans/manim-slides/pull/506)

(v5.1.10)=
## [v5.1.10](https://github.com/jeertmans/manim-slides/compare/v5.1.9...v5.1.10)

(v5.1.10-added)=
### Added

- Added `--offline` option to `manim-slides convert` for offline
  HTML presentations.
  [#440](https://github.com/jeertmans/manim-slides/pull/440)
- Added documentation to config option to `manim-slides convert`
  when using `--show-config`.
  [#485](https://github.com/jeertmans/manim-slides/pull/485)

(v5.1.10-changed)=
### Changed

- Allow multiple slide reverses by going backward [@PeculiarProgrammer](https://github.com/PeculiarProgrammer).
  [#488](https://github.com/jeertmans/manim-slides/pull/488)

(v5.1.10-fixed)=
### Fixed

- Fixed PyAV issue by pinning its version to `<14`.
  A future release will contain a fix that supports both `av>=14`
  and `av<14`, as their syntax differ, but the former doesn't
  provide binary wheels for Python 3.9.
  [#494](https://github.com/jeertmans/manim-slides/pull/494)
- Fixed blank web page when converting multiple slides into HTML.
  [#497](https://github.com/jeertmans/manim-slides/pull/497)

(v5.1.9)=
## [v5.1.9](https://github.com/jeertmans/manim-slides/compare/v5.1.8...v5.1.9)

(v5.1.9-fixed)=
## Chore

- Fixed failing docker builds.
  [#481](https://github.com/jeertmans/manim-slides/pull/481)

(v5.1.8)=
## [v5.1.8](https://github.com/jeertmans/manim-slides/compare/v5.1.7...v5.1.8)

(v5.1.8-added)=
### Added

- Added `manim-slides checkhealth` command to easily obtain important information
  for debug purposes.
  [#458](https://github.com/jeertmans/manim-slides/pull/458)
- Added support for `disable_caching` and `flush_cache` options from Manim, and
  also the possibility to configure them through class options.
  [#452](https://github.com/jeertmans/manim-slides/pull/452)
- Added `--to=zip` convert format to generate an archive with HTML output
  and asset files.
  [#470](https://github.com/jeertmans/manim-slides/pull/470)

(v5.1.8-chore)=
### Chore

- Pinned `rtoml==0.9.0` on Windows platforms,
  see [#398](https://github.com/jeertmans/manim-slides/pull/398),
  until
  [samuelcolvin/rtoml#74](https://github.com/samuelcolvin/rtoml/issues/74)
  is solved.
  [#432](https://github.com/jeertmans/manim-slides/pull/432)
- Removed an old validation check that prevented setting `loop=True` with
  `auto_next=True` on `next_slide()`
  [#445](https://github.com/jeertmans/manim-slides/pull/445)
- Improved (and fixed) tests for Manim(GL), bumped minimal ManimCE version,
  improved coverage, and override dependency conflicts.
  [#447](https://github.com/jeertmans/manim-slides/pull/447)
- Improved issue templates.
  [#456](https://github.com/jeertmans/manim-slides/pull/456)
- Enhanced the error message when the slides folder does not exist.
  [#462](https://github.com/jeertmans/manim-slides/pull/462)
- Fixed deprecation warnings.
  [#467](https://github.com/jeertmans/manim-slides/pull/467)
- Documented potential fix for PPTX issue.
  [#475](https://github.com/jeertmans/manim-slides/pull/475)
- Changed project manager from Rye to uv.
  [#476](https://github.com/jeertmans/manim-slides/pull/476)

(v5.1.8-fixed)=
### Fixed

- Fix combining assets from multiple scenes to avoid filename collision.
  [#429](https://github.com/jeertmans/manim-slides/pull/429)
- Fixed whitespace issue in default RevealJS template.
  [#442](https://github.com/jeertmans/manim-slides/pull/442)
- Fixed black screen issue on recent Qt versions and device loss detected,
  thanks to [@PeculiarProgrammer](https://github.com/PeculiarProgrammer)!
  [#465](https://github.com/jeertmans/manim-slides/pull/465)

(v5.1.8-removed)=
### Removed

- Removed `full-gl` extra, because it does not make sense to ship both
  `manimgl` and `manim` together.
  [#447](https://github.com/jeertmans/manim-slides/pull/447)

(v5.1.7)=
## [v5.1.7](https://github.com/jeertmans/manim-slides/compare/v5.1.6...v5.1.7)

(v5.1.7-chore)=
### Chore

- Improved the CI for bumping the version and README rendering on PyPI.
  [#425](https://github.com/jeertmans/manim-slides/pull/425)

(v5.1.6)=
## [v5.1.6](https://github.com/jeertmans/manim-slides/compare/v5.1.5...v5.1.6)

(v5.1.6-added)=
### Added

- Added options to skip the Manim Slides Sphinx directive.
  [#423](https://github.com/jeertmans/manim-slides/pull/423)

(v5.1.6-chore)=
### Chore

- Added an examples gallery.
  [#422](https://github.com/jeertmans/manim-slides/pull/422)

(v5.1.5)=
## [v5.1.5](https://github.com/jeertmans/manim-slides/compare/v5.1.4...v5.1.5)

(v5.1.5-chore)=
### Chore

- Added CI for broken HTML links and fixed, plus spell checking.
  [#417](https://github.com/jeertmans/manim-slides/pull/417)
- Create FAQ page and clear FAQ from README.md.
  [#418](https://github.com/jeertmans/manim-slides/pull/418)
- Used Rye instead of PDM for faster development.
  [#420](https://github.com/jeertmans/manim-slides/pull/420)

(v5.1.5-fixed)=
### Fixed

- Fixed broken `--show-config` command.
  [#419](https://github.com/jeertmans/manim-slides/pull/419)

(v5.1.4)=
## [v5.1.4](https://github.com/jeertmans/manim-slides/compare/v5.1.3...v5.1.4)

(v5.1.4-added)=
### Added

- Added audio output to `manim-slides present`.
  [#382](https://github.com/jeertmans/manim-slides/pull/382)

(v5.1.4-changed)=
### Changed

- Added `--info-window-screen` option and change `--screen-number`
  to not move the info window.
  [#389](https://github.com/jeertmans/manim-slides/pull/389)

(v5.1.4-chore)=
### Chore

- Created a favicon for the website/documentation.
  [#399](https://github.com/jeertmans/manim-slides/pull/399)
- Documented the Nixpkg installation.
  [#404](https://github.com/jeertmans/manim-slides/pull/404 )
- Updated the default RevealJS version to 5.1.0.
  [#412](https://github.com/jeertmans/manim-slides/pull/412)
- Removed the `opencv-python` dependency.
  [#415](https://github.com/jeertmans/manim-slides/pull/415)

(v5.1.4-fixed)=
### Fixed

- Fixed the retrieval of `background_color` with ManimCE.
  [#414](https://github.com/jeertmans/manim-slides/pull/414)
- Fixed #390 issue caused by empty media created by ManimCE.
  [#416](https://github.com/jeertmans/manim-slides/pull/416)

(v5.1.3)=
## [v5.1.3](https://github.com/jeertmans/manim-slides/compare/v5.1.2...v5.1.3)

(v5.1.3-chore)=
### Chore

- Fix link in documentation.
  [#368](https://github.com/jeertmans/manim-slides/pull/368)

- Warn users if not using recommended Qt bindings.
  [#373](https://github.com/jeertmans/manim-slides/pull/373)

(v5.1.2)=
## [v5.1.2](https://github.com/jeertmans/manim-slides/compare/v5.1.1...v5.1.2)

(v5.1.2-chore)=
### Chore

- Fix ReadTheDocs version flyout in iframes.
  [#367](https://github.com/jeertmans/manim-slides/pull/367)

(v5.1.1)=
## [v5.1.1](https://github.com/jeertmans/manim-slides/compare/v5.1.0...v5.1.1)

(v5.1.1-chore)=
### Chore

- Move documentation to ReadTheDocs for better versioning.
  [#365](https://github.com/jeertmans/manim-slides/pull/365)

(v5.1)=
## [v5.1](https://github.com/jeertmans/manim-slides/compare/v5.0.0...v5.1.0)

(v5.1-added)=
### Added

- Added the `--hide-info-window` option to `manim-slides present`.
  [#313](https://github.com/jeertmans/manim-slides/pull/313)
- Added the `manim-slides render` command
  to render slides using correct Manim installation.
  [#317](https://github.com/jeertmans/manim-slides/pull/317)
- Added the `playback-rate` and `reversed-playback-rate` options
  to slide config.
  [#320](https://github.com/jeertmans/manim-slides/pull/320)
- Added the speaker notes option.
  [#322](https://github.com/jeertmans/manim-slides/pull/322)
- Added `auto` option for conversion format, which is the default.
  This is somewhat a **breaking change**, but changes to the CLI
  API are not considered to be very important.
  [#325](https://github.com/jeertmans/manim-slides/pull/325)
- Added `return_animation` option to slide animations `self.wipe`
  and `self.zoom`.
  [#331](https://github.com/jeertmans/manim-slides/pull/331)
- Created a Docker image, published on GitHub.
  [#355](https://github.com/jeertmans/manim-slides/pull/355)
- Added `:template:` and `:config_options` options to
  the Sphinx directive.
  [#357](https://github.com/jeertmans/manim-slides/pull/357)

(v5.1-modified)=
### Modified

- Modified the internal logic to simplify adding configuration options.
  [#321](https://github.com/jeertmans/manim-slides/pull/321)
- Remove `reversed` file assets when exporting to HTML, as it was not used.
  [#336](https://github.com/jeertmans/manim-slides/pull/336)

(v5.1-chore)=
### Chore

- Removed subrocess calls to FFmpeg with direct `libav` bindings using
  the `av` Python module. This should enhance rendering speed and security.
  [#335](https://github.com/jeertmans/manim-slides/pull/335)
- Changed build backend to PDM and reflected on docs.
  [#354](https://github.com/jeertmans/manim-slides/pull/354)
- Dropped Python 3.8 support.
  [#350](https://github.com/jeertmans/manim-slides/pull/350)
- Made Qt backend optional and support PyQt6 too.
  [#350](https://github.com/jeertmans/manim-slides/pull/350)
- Documentated how to create and use a custom HTML template.
  [#357](https://github.com/jeertmans/manim-slides/pull/357)

## [v5](https://github.com/jeertmans/manim-slides/compare/v4.16.0...v5.0.0)

Prior to v5, there was no real CHANGELOG other than the GitHub releases,
with most of the content automatically generated by GitHub from merged
pull requests.

In an effort to better document changes, this CHANGELOG document is now created.

(v5-added)=
### Added

- Added the following option aliases to `manim-slides present`:
  `-F` and `--full-screen` for `fullscreen`,
  `-H` for `--hide-mouse`,
  and `-S` for `--screen-number`.
  [#243](https://github.com/jeertmans/manim-slides/pull/243)
- Added a full screen key binding (defaults to <kbd>F</kbd>) in the
  presenter.
  [#243](https://github.com/jeertmans/manim-slides/pull/243)
- Added support for including code from a file in Manim Slides
  Sphinx directive.
  [#261](https://github.com/jeertmans/manim-slides/pull/261)
- Added the `manim_slides.slide.animation` module and created the
  `Wipe` and `Zoom` classes, that return a new animation.
  [#285](https://github.com/jeertmans/manim-slides/pull/285)
- Added two environ variables, `MANIM_API` and `FORCE_MANIM_API`,
  to specify the `MANIM_API` to be used: `manim` and `manimce` will
  import `manim`, while `manimgl` and `manimlib` will import `manimlib`.
  If one of the two APIs is already imported, use `FORCE_MANIM_API=1` to
  override this.
  [#285](https://github.com/jeertmans/manim-slides/pull/285)
- Added a working `ThreeDSlide` class compatible with `manimlib`.
  [#285](https://github.com/jeertmans/manim-slides/pull/285)
- Added `loop` option to `Slide`'s `next_slide` method.
  Calling `next_slide` will never fail anymore.
  [#294](https://github.com/jeertmans/manim-slides/pull/294)
- Added `Slide.next_section` for compatibility with `manim`'s
  `Scene.next_section` method.
  [#295](https://github.com/jeertmans/manim-slides/pull/295)
- Added `--next-terminates-loop` option to `manim-slides present` for turn a
  looping slide into a normal one, so that it ends nicely. This is useful to
  have a smooth transition with the next slide.
  [#299](https://github.com/jeertmans/manim-slides/pull/299)
- Added `--playback-rate` option to `manim-slides present` for testing purposes.
  [#300](https://github.com/jeertmans/manim-slides/pull/300)
- Added `auto_next` option to `Slide`'s `next_slide` method to automatically
  play the next slide upon terminating. Supported by `present` and
  `convert --to=html` commands.
  [#304](https://github.com/jeertmans/manim-slides/pull/304)

(v5-changed)=
### Changed

- Automatically concatenate all animations from a slide into one.
  This is a **breaking change** because the config file format is
  different from the previous one. For migration help, see associated PR.
  [#242](https://github.com/jeertmans/manim-slides/pull/242)
- Changed the player interface to only use PySide6, and not a combination of
  PySide6 and OpenCV. A few features have been removed (see removed section),
  but the new player should be much easier to maintain and more performant,
  than its predecessor.
  [#243](https://github.com/jeertmans/manim-slides/pull/243)
- Changed the slide config format to exclude unnecessary information.
  `StypeType` is removed in favor to one boolean `loop` field. This is
  a **breaking change** and one should re-render the slides to apply changes.
  [#243](https://github.com/jeertmans/manim-slides/pull/243)
- Renamed key bindings in the config. This is a **breaking change** and one
  should either manually rename them (see list below) or re-init a config.
  List of changes: `CONTINUE` to `NEXT`, `BACK` to `PREVIOUS`, and
  `REWIND` to `REPLAY`.
  [#243](https://github.com/jeertmans/manim-slides/pull/243)
- Conversion to HTML now uses Jinja2 templating. The template file has
  been modified accordingly, and old templates will not work anymore.
  This is a **breaking change**.
  [#271](https://github.com/jeertmans/manim-slides/pull/271)
- Bumped RevealJS' default version to v4.6.1, and added three new themes.
  [#272](https://github.com/jeertmans/manim-slides/pull/272)
- Changed the logger such that `make_logger` is called at module import,
  and we do not use Manim's logger anymore.
  [#285](https://github.com/jeertmans/manim-slides/pull/285)
- Changed `Slide.wipe` and `Slide.zoom` to automatically call `self.play`.
  This is a **breaking change** as calling `self.play(self.wipe(...))` now
  raises an error (because `None` is not an animation).
  [#285](https://github.com/jeertmans/manim-slides/pull/285)
- Changed the `manim_slides.slide` module to contain submodules, i.e.,
  `slide.manim`, `slide.manimlib`, `slide.animation`.
  Only `slide.animation` is part of the public API.
  Rules for choosing the Manim API (either `manim` or `manimlib`) has changed,
  and defaults to the currently imported module, with a preference for `manim`.
  [#285](https://github.com/jeertmans/manim-slides/pull/285)

(v5-fixed)=
### Fixed

- Patched enums in `manim_slides/convert.py` to correctly call `str`'s
  `__str__` method, and not the `Enum` one.
  This bug was discovered by
  [@alexanderskulikov](https://github.com/alexanderskulikov) in
  [#253](https://github.com/jeertmans/manim-slides/discussions/253), caused by
  Python 3.11's change in how `Enum` work.
  [#257](https://github.com/jeertmans/manim-slides/pull/257).
- Fixed potential non-existing parent path issue in
  `manim convert`'s destination path.
  [#262](https://github.com/jeertmans/manim-slides/pull/262)

(v5-removed)=
### Removed

- Removed `--start-at-animation-number` option from `manim-slides present`.
  [#242](https://github.com/jeertmans/manim-slides/pull/242)
- Removed the following options from `manim-slides present`:
  `--resolution`, `--record-to`, `--resize-mode`, and `--background-color`.
  [#243](https://github.com/jeertmans/manim-slides/pull/243)
- Removed `PERF` verbosity level because not used anymore.
  [#245](https://github.com/jeertmans/manim-slides/pull/245)
- Remove `Slide`'s method `start_loop` and `self.end_loop`
  in favor to `self.next_slide(loop=True)`.
  This is a **breaking change**.
  [#294](https://github.com/jeertmans/manim-slides/pull/294)

<!-- end changelog -->
