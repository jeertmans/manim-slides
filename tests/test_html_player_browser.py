import hashlib
import io
import os
from pathlib import Path

import av
import numpy as np
import pytest
from PIL import Image

from manim_slides.config import PresentationConfig, SlideConfig
from manim_slides.convert import HtmlPlayer

playwright = pytest.importorskip("playwright.sync_api")

pytestmark = pytest.mark.skipif(
    os.environ.get("MANIM_SLIDES_BROWSER_TESTS") != "1",
    reason="set MANIM_SLIDES_BROWSER_TESTS=1 to run real-browser tests",
)


def make_video(
    path: Path, start: tuple[int, int, int], end: tuple[int, int, int]
) -> None:
    container = av.open(str(path), "w")
    stream = container.add_stream("libx264", rate=15)
    stream.width = 160
    stream.height = 90
    stream.pix_fmt = "yuv420p"
    stream.options = {"preset": "ultrafast", "crf": "18"}
    for index in range(15):
        ratio = index / 14
        color = np.array(
            [round(a + (b - a) * ratio) for a, b in zip(start, end, strict=True)],
            dtype=np.uint8,
        )
        pixels = np.empty((90, 160, 3), dtype=np.uint8)
        pixels[:] = color
        frame = av.VideoFrame.from_ndarray(pixels, format="rgb24")
        for packet in stream.encode(frame):
            container.mux(packet)
    for packet in stream.encode():
        container.mux(packet)
    container.close()


def make_motion_video(path: Path, *, reverse: bool = False) -> None:
    container = av.open(str(path), "w")
    stream = container.add_stream("libx264", rate=15)
    stream.width = 160
    stream.height = 90
    stream.pix_fmt = "yuv420p"
    stream.options = {"preset": "ultrafast", "crf": "18"}
    for index in range(30):
        position = 29 - index if reverse else index
        left = round(8 + 134 * position / 29)
        pixels = np.zeros((90, 160, 3), dtype=np.uint8)
        pixels[44:46, 8:152] = (40, 100, 220)
        pixels[35:55, left : left + 18] = (230, 40, 40)
        frame = av.VideoFrame.from_ndarray(pixels, format="rgb24")
        for packet in stream.encode(frame):
            container.mux(packet)
    for packet in stream.encode():
        container.mux(packet)
    container.close()


@pytest.fixture
def color_config(tmp_path: Path) -> PresentationConfig:
    red, green, blue = (220, 20, 20), (20, 210, 20), (20, 20, 220)
    paths = {}
    for name, start, end in (
        ("zero-forward", red, green),
        ("zero-reverse", green, red),
        ("one-forward", green, blue),
        ("one-reverse", blue, green),
    ):
        path = tmp_path / f"{name}.mp4"
        make_video(path, start, end)
        paths[name] = path
    return PresentationConfig(
        slides=[
            SlideConfig(
                file=paths["zero-forward"],
                rev_file=paths["zero-reverse"],
                notes='<img src=x onerror="globalThis.notesExecuted=true">Safe note',
            ),
            SlideConfig(
                file=paths["one-forward"],
                rev_file=paths["one-reverse"],
                direction="vertical",
                notes="Second note",
            ),
        ],
        resolution=(160, 90),
        background_color="black",
    )


@pytest.fixture
def motion_config(tmp_path: Path) -> PresentationConfig:
    forward = tmp_path / "motion-forward.mp4"
    reverse = tmp_path / "motion-reverse.mp4"
    make_motion_video(forward)
    make_motion_video(reverse, reverse=True)
    return PresentationConfig(
        slides=[
            SlideConfig(file=forward, rev_file=reverse),
            SlideConfig(file=forward, rev_file=reverse),
        ],
        resolution=(160, 90),
        background_color="black",
    )


@pytest.fixture(scope="module")
def browser():
    with playwright.sync_playwright() as instance:
        browser = instance.chromium.launch(
            args=["--autoplay-policy=no-user-gesture-required"]
        )
        yield browser
        browser.close()


def open_portable(browser, output: Path, **context_options):
    context = browser.new_context(**context_options)
    context.route("http://**", lambda route: route.abort())
    context.route("https://**", lambda route: route.abort())
    page = context.new_page()
    requests = []
    page.on("request", lambda request: requests.append(request.url))
    page.goto(output.resolve().as_uri())
    return context, page, requests


def wait_held(page, index: int) -> None:
    page.locator("[data-ms-player]").wait_for(state="visible")
    page.wait_for_function(
        "!['loading', 'transitioning', 'ready-at-start'].includes("
        "document.querySelector('[data-ms-player]').dataset.state)",
        timeout=10_000,
    )
    if page.locator("[data-ms-player]").get_attribute("data-state") == "paused":
        page.locator("[data-ms-gesture]").click()
    page.wait_for_function(
        "([index]) => { const p = document.querySelector('[data-ms-player]'); "
        "return p.dataset.state === 'held-at-end' && Number(p.dataset.slideIndex) === index; }",
        arg=[index],
        timeout=10_000,
    )


def center_rgb(page) -> tuple[int, int, int]:
    screenshot = page.locator("[data-ms-stage]").screenshot()
    image = Image.open(io.BytesIO(screenshot)).convert("RGB")
    pixel = image.getpixel((image.width // 2, image.height // 2))
    assert isinstance(pixel, tuple)
    return int(pixel[0]), int(pixel[1]), int(pixel[2])


def active_video_telemetry(page) -> dict[str, object]:
    value = page.evaluate(
        """() => {
          const player = document.querySelector('[data-ms-player]');
          const video = player.manimSlidesPlayer.currentVideo();
          return {
            attributeSrc: video.getAttribute('src'),
            src: video.src,
            currentSrc: video.currentSrc,
            currentTime: video.currentTime,
            duration: video.duration,
            paused: video.paused,
          };
        }"""
    )
    assert isinstance(value, dict)
    return value


def wait_playing_and_assert_time_advances(page, role: str) -> None:
    page.wait_for_function(
        "role => document.querySelector('[data-ms-player]').dataset.state === role",
        arg=role,
        timeout=10_000,
    )
    start = active_video_telemetry(page)["currentTime"]
    assert isinstance(start, (int, float))
    page.wait_for_function(
        "start => document.querySelector('[data-ms-player]').manimSlidesPlayer"
        ".currentVideo().currentTime > start + 0.12",
        arg=start,
        timeout=3_000,
    )


def assert_blob_source_is_not_document(page, output: Path) -> None:
    telemetry = active_video_telemetry(page)
    assert isinstance(telemetry["attributeSrc"], str)
    assert telemetry["attributeSrc"].startswith("blob:")
    assert telemetry["src"] == telemetry["currentSrc"]
    assert telemetry["src"] != output.resolve().as_uri()
    assert page.evaluate(
        "[...document.querySelectorAll('video')].every(video => video.src !== location.href)"
    )


def swipe(
    page,
    *,
    pointer_id: int,
    start: tuple[int, int],
    end: tuple[int, int],
) -> None:
    stage = page.locator("[data-ms-stage]")
    common = {"pointerId": pointer_id, "pointerType": "touch", "isPrimary": True}
    stage.dispatch_event(
        "pointerdown",
        {**common, "button": 0, "clientX": start[0], "clientY": start[1]},
    )
    stage.dispatch_event(
        "pointermove", {**common, "clientX": end[0], "clientY": end[1]}
    )
    stage.dispatch_event(
        "pointerup",
        {**common, "button": 0, "clientX": end[0], "clientY": end[1]},
    )


def test_file_portable_motion_preferences_and_explicit_playback(
    browser, tmp_path: Path, motion_config: PresentationConfig
) -> None:
    output = tmp_path / "motion.html"
    HtmlPlayer(presentation_configs=[motion_config], one_file=True).convert_to(output)

    context, page, requests = open_portable(
        browser, output, reduced_motion="no-preference"
    )
    page.wait_for_function(
        "document.querySelector('[data-ms-player]')?.manimSlidesPlayer"
        "?.currentVideo()?.currentSrc"
    )
    assert_blob_source_is_not_document(page, output)
    wait_playing_and_assert_time_advances(page, "playing-forward")
    page.keyboard.press("Space")
    wait_held(page, 0)

    page.keyboard.press("Space")
    wait_playing_and_assert_time_advances(page, "playing-forward")
    wait_held(page, 1)
    page.locator("nav [data-command=back]").click()
    wait_playing_and_assert_time_advances(page, "playing-reverse")
    page.locator("nav [data-command=back]").click()
    wait_held(page, 0)
    page.locator("[data-command=replay]").click()
    wait_playing_and_assert_time_advances(page, "playing-forward")
    assert all(not url.startswith(("http://", "https://")) for url in requests)
    context.close()

    context, page, requests = open_portable(browser, output, reduced_motion="reduce")
    page.wait_for_function(
        "document.querySelector('[data-ms-player]')?.dataset.state === 'paused'"
    )
    assert page.evaluate("matchMedia('(prefers-reduced-motion: reduce)').matches")
    assert_blob_source_is_not_document(page, output)
    before = active_video_telemetry(page)["currentTime"]
    page.wait_for_timeout(300)
    after = active_video_telemetry(page)["currentTime"]
    assert isinstance(before, (int, float))
    assert isinstance(after, (int, float))
    assert before < 0.05
    assert after == pytest.approx(before, abs=0.02)
    assert page.locator("[data-ms-gesture]").is_visible()
    assert page.locator("[data-ms-gesture]").text_content() == "Play animation"
    page.locator("[data-ms-gesture]").click()
    assert (
        page.locator("[data-ms-player]").get_attribute("data-animation-opt-in")
        == "true"
    )
    wait_playing_and_assert_time_advances(page, "playing-forward")

    page.locator("nav [data-command=next]").click()
    wait_held(page, 0)
    page.locator("nav [data-command=next]").click()
    wait_playing_and_assert_time_advances(page, "playing-forward")
    assert not page.locator("[data-ms-gesture]").is_visible()
    wait_held(page, 1)
    page.locator("nav [data-command=back]").click()
    wait_playing_and_assert_time_advances(page, "playing-reverse")
    page.locator("nav [data-command=back]").click()
    wait_held(page, 0)
    page.locator("[data-command=replay]").click()
    wait_playing_and_assert_time_advances(page, "playing-forward")
    assert all(not url.startswith(("http://", "https://")) for url in requests)
    context.close()


def test_forward_click_and_visible_next_are_two_step_intents(
    browser, tmp_path: Path, motion_config: PresentationConfig
) -> None:
    output = tmp_path / "forward-intents.html"
    HtmlPlayer(presentation_configs=[motion_config], one_file=True).convert_to(output)
    context, page, requests = open_portable(browser, output)

    wait_playing_and_assert_time_advances(page, "playing-forward")
    page.locator("nav [data-command=next]").click()
    wait_held(page, 0)
    page.locator("nav [data-command=next]").click()
    wait_playing_and_assert_time_advances(page, "playing-forward")
    wait_held(page, 1)

    page.keyboard.press("ArrowLeft")
    wait_held(page, 0)
    page.keyboard.press("r")
    wait_playing_and_assert_time_advances(page, "playing-forward")
    page.locator("[data-ms-stage]").click(position={"x": 300, "y": 180})
    wait_held(page, 0)
    page.locator("[data-ms-stage]").click(position={"x": 300, "y": 180})
    wait_playing_and_assert_time_advances(page, "playing-forward")
    assert page.locator("[data-ms-player]").get_attribute("data-slide-index") == "1"
    assert all(not url.startswith(("http://", "https://")) for url in requests)
    context.close()


def test_present_mode_consent_chrome_overlays_and_fullscreen_rejection(
    browser, tmp_path: Path, motion_config: PresentationConfig
) -> None:
    output = tmp_path / "present-rejected.html"
    HtmlPlayer(presentation_configs=[motion_config], one_file=True).convert_to(output)
    context = browser.new_context(reduced_motion="reduce")
    context.route("http://**", lambda route: route.abort())
    context.route("https://**", lambda route: route.abort())
    page = context.new_page()
    requests = []
    page.on("request", lambda request: requests.append(request.url))
    page.add_init_script(
        """
        Object.defineProperty(Element.prototype, 'requestFullscreen', {
          configurable: true,
          value() { return Promise.reject(new DOMException('denied', 'NotAllowedError')); },
        });
        """
    )
    page.goto(output.resolve().as_uri())
    page.wait_for_function(
        "document.querySelector('[data-ms-player]').dataset.state === 'paused'"
    )

    page.get_by_role("button", name="Enter presentation mode").click()
    wait_playing_and_assert_time_advances(page, "playing-forward")
    player = page.locator("[data-ms-player]")
    assert player.get_attribute("data-presenting") == "true"
    assert player.get_attribute("data-animation-opt-in") == "true"
    assert player.evaluate("node => node === document.activeElement")
    for selector in (".ms-controls", ".ms-position", ".ms-progress"):
        assert (
            page.locator(selector).evaluate("node => getComputedStyle(node).display")
            == "none"
        )

    page.keyboard.press("p")
    assert player.get_attribute("data-state") == "paused"
    page.keyboard.press("p")
    wait_playing_and_assert_time_advances(page, "playing-forward")
    page.keyboard.press("r")
    wait_playing_and_assert_time_advances(page, "playing-forward")
    page.keyboard.press("?")
    assert page.locator("[data-ms-help]").is_visible()
    page.keyboard.press("Escape")
    assert not page.locator("[data-ms-help]").is_visible()
    assert player.get_attribute("data-presenting") == "true"
    page.keyboard.press("o")
    assert page.locator("[data-ms-overview]").is_visible()
    page.keyboard.press("Escape")
    assert not page.locator("[data-ms-overview]").is_visible()
    assert player.get_attribute("data-presenting") == "true"

    page.keyboard.press("Escape")
    page.wait_for_function(
        "document.querySelector('[data-ms-player]').dataset.presenting === 'false'"
    )
    assert (
        page.locator(".ms-controls").evaluate("node => getComputedStyle(node).display")
        != "none"
    )
    assert all(not url.startswith(("http://", "https://")) for url in requests)
    context.close()


def test_present_fullscreen_exit_synchronizes_and_f_toggles_mode(
    browser, tmp_path: Path, motion_config: PresentationConfig
) -> None:
    output = tmp_path / "present-fullscreen.html"
    HtmlPlayer(presentation_configs=[motion_config], one_file=True).convert_to(output)
    context, page, _requests = open_portable(browser, output)
    wait_playing_and_assert_time_advances(page, "playing-forward")

    page.get_by_role("button", name="Enter presentation mode").click()
    page.wait_for_function(
        "document.fullscreenElement === document.querySelector('[data-ms-player]')"
    )
    page.evaluate("document.exitFullscreen()")
    page.wait_for_function(
        "document.querySelector('[data-ms-player]').dataset.presenting === 'false'"
    )

    page.locator("[data-ms-player]").focus()
    page.keyboard.press("f")
    page.wait_for_function(
        "document.querySelector('[data-ms-player]').dataset.presenting === 'true'"
    )
    page.keyboard.press("f")
    page.wait_for_function(
        "document.querySelector('[data-ms-player]').dataset.presenting === 'false'"
    )
    context.close()


def test_file_portable_navigation_reverse_pixels_and_cleanup(
    browser, tmp_path: Path, color_config: PresentationConfig
) -> None:
    output = tmp_path / "portable.html"
    HtmlPlayer(presentation_configs=[color_config], one_file=True).convert_to(output)
    context, page, requests = open_portable(
        browser, output, viewport={"width": 800, "height": 450}
    )
    wait_held(page, 0)
    page.keyboard.press("ArrowRight")
    wait_held(page, 1)
    assert center_rgb(page)[2] > 150

    page.keyboard.press("ArrowLeft")
    samples = []
    for _ in range(8):
        page.wait_for_timeout(70)
        samples.append(center_rgb(page))
    wait_held(page, 0)
    assert all(red < 90 for red, _green, _blue in samples)
    final = center_rgb(page)
    assert final[1] > 150 and final[0] < 90 and final[2] < 90
    assert all(not url.startswith(("http://", "https://")) for url in requests)

    assert (
        page.evaluate(
            "document.querySelector('[data-ms-player]').manimSlidesPlayer.assetStore.urls.size"
        )
        > 0
    )
    page.evaluate(
        "document.querySelector('[data-ms-player]').manimSlidesPlayer.destroy()"
    )
    assert (
        page.evaluate(
            "document.querySelector('[data-ms-player]').manimSlidesPlayer.assetStore.urls.size"
        )
        == 0
    )
    context.close()


def test_keyboard_click_notes_focus_and_rapid_input(
    browser, tmp_path: Path, color_config: PresentationConfig
) -> None:
    output = tmp_path / "inputs.html"
    HtmlPlayer(presentation_configs=[color_config], one_file=True).convert_to(output)
    text = output.read_text(encoding="utf-8").replace(
        '<main class="manim-slides-player" data-ms-player data-ms-standalone',
        '<input id="host-input" aria-label="Host input">\n'
        '<main class="manim-slides-player" data-ms-player',
    )
    output.write_text(text, encoding="utf-8")
    context, page, _requests = open_portable(browser, output)
    wait_held(page, 0)

    page.locator("#host-input").focus()
    page.keyboard.press("ArrowRight")
    assert page.locator("[data-ms-player]").get_attribute("data-slide-index") == "0"
    page.locator("[data-ms-player]").focus()
    page.keyboard.press("Space")
    wait_held(page, 1)
    page.keyboard.press("PageUp")
    wait_held(page, 0)
    page.keyboard.press("PageDown")
    wait_held(page, 1)
    page.keyboard.press("ArrowLeft")
    wait_held(page, 0)

    page.locator("[data-command=notes]").click()
    assert "Safe note" in page.locator("[data-ms-notes-text]").text_content()
    assert page.evaluate("globalThis.notesExecuted") is None
    page.locator("[data-command=notes]").click()

    page.keyboard.press("o")
    assert page.locator("[data-ms-overview]").is_visible()
    page.locator("[data-ms-overview-list] button").nth(1).click()
    wait_held(page, 1)
    page.keyboard.press("ArrowLeft")
    wait_held(page, 0)
    page.keyboard.press("?")
    assert page.locator("[data-ms-help]").is_visible()
    page.keyboard.press("Escape")
    assert not page.locator("[data-ms-help]").is_visible()

    page.locator("[data-ms-stage]").click(position={"x": 300, "y": 180})
    page.keyboard.press("ArrowLeft")
    page.keyboard.press("ArrowRight")
    page.keyboard.press("ArrowLeft")
    page.keyboard.press("ArrowRight")
    page.wait_for_timeout(1400)
    assert page.locator("[data-ms-player]").get_attribute("data-state") != "failed"
    context.close()


def test_mobile_swipe_resize_and_autoplay_recovery(
    browser, tmp_path: Path, color_config: PresentationConfig
) -> None:
    output = tmp_path / "mobile.html"
    HtmlPlayer(presentation_configs=[color_config], one_file=True).convert_to(output)
    context = browser.new_context(
        viewport={"width": 390, "height": 844}, has_touch=True, is_mobile=True
    )
    page = context.new_page()
    page.add_init_script(
        """
        const nativePlay = HTMLMediaElement.prototype.play;
        let rejected = false;
        HTMLMediaElement.prototype.play = function () {
          if (!rejected) {
            rejected = true;
            return Promise.reject(new DOMException('gesture required', 'NotAllowedError'));
          }
          return nativePlay.call(this);
        };
        """
    )
    page.goto(output.resolve().as_uri())
    page.wait_for_function(
        "document.querySelector('[data-ms-player]').dataset.state === 'paused'"
    )
    assert page.locator("[data-ms-gesture]").is_visible()
    page.locator("[data-ms-gesture]").click()
    wait_playing_and_assert_time_advances(page, "playing-forward")

    swipe(page, pointer_id=1, start=(330, 400), end=(80, 400))
    wait_held(page, 0)
    swipe(page, pointer_id=2, start=(330, 400), end=(80, 400))
    wait_held(page, 1)
    page.set_viewport_size({"width": 844, "height": 390})
    assert page.locator("[data-ms-player]").bounding_box()["width"] == pytest.approx(
        844, abs=1
    )

    swipe(page, pointer_id=3, start=(400, 80), end=(400, 300))
    wait_held(page, 0)
    context.close()


def test_loop_auto_next_pause_replay_and_error_state(
    browser, tmp_path: Path, color_config: PresentationConfig
) -> None:
    slides = [
        color_config.slides[0].model_copy(update={"auto_next": True}),
        color_config.slides[1].model_copy(update={"loop": True}),
    ]
    output = tmp_path / "metadata.html"
    HtmlPlayer(
        presentation_configs=[PresentationConfig(slides=slides, resolution=(160, 90))]
    ).convert_to(output)
    context, page, _requests = open_portable(browser, output)
    page.wait_for_function(
        "document.querySelector('[data-ms-player]').dataset.slideIndex === '1'",
        timeout=10_000,
    )
    page.wait_for_timeout(1200)
    assert (
        page.locator("[data-ms-player]").get_attribute("data-state")
        == "playing-forward"
    )
    page.locator("[data-command=pause]").click()
    assert page.locator("[data-ms-player]").get_attribute("data-state") == "paused"
    page.locator("[data-command=pause]").click()
    page.locator("[data-command=replay]").click()
    assert page.locator("[data-ms-player]").get_attribute("data-state") in {
        "transitioning",
        "playing-forward",
        "ready-at-start",
    }
    context.close()

    broken = tmp_path / "broken.html"
    HtmlPlayer(presentation_configs=[color_config]).convert_to(broken)
    digest = hashlib.sha256(color_config.slides[0].file.read_bytes()).hexdigest()[:16]
    asset = next((tmp_path / "broken_assets").glob(f"media-{digest}.*"))
    asset.unlink()
    context, page, _requests = open_portable(browser, broken)
    page.wait_for_function(
        "document.querySelector('[data-ms-player]').dataset.state === 'failed'",
        timeout=10_000,
    )
    assert (
        "Slide 1 forward asset"
        in page.locator("[data-ms-error-message]").text_content()
    )
    context.close()
