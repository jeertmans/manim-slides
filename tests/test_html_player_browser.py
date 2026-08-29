import io
import hashlib
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


def make_video(path: Path, start: tuple[int, int, int], end: tuple[int, int, int]) -> None:
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


@pytest.fixture(scope="module")
def browser():
    with playwright.sync_playwright() as instance:
        browser = instance.chromium.launch()
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
    page.evaluate("document.querySelector('[data-ms-player]').manimSlidesPlayer.destroy()")
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
    wait_held(page, 0)

    stage = page.locator("[data-ms-stage]")
    stage.dispatch_event(
        "pointerdown",
        {
            "pointerId": 1,
            "pointerType": "touch",
            "isPrimary": True,
            "button": 0,
            "clientX": 330,
            "clientY": 400,
        },
    )
    stage.dispatch_event(
        "pointermove",
        {
            "pointerId": 1,
            "pointerType": "touch",
            "isPrimary": True,
            "clientX": 80,
            "clientY": 400,
        },
    )
    stage.dispatch_event(
        "pointerup",
        {
            "pointerId": 1,
            "pointerType": "touch",
            "isPrimary": True,
            "button": 0,
            "clientX": 80,
            "clientY": 400,
        },
    )
    wait_held(page, 1)
    page.set_viewport_size({"width": 844, "height": 390})
    assert page.locator("[data-ms-player]").bounding_box()["width"] == pytest.approx(
        844, abs=1
    )

    stage.dispatch_event(
        "pointerdown",
        {
            "pointerId": 2,
            "pointerType": "touch",
            "isPrimary": True,
            "button": 0,
            "clientX": 400,
            "clientY": 80,
        },
    )
    stage.dispatch_event(
        "pointermove",
        {
            "pointerId": 2,
            "pointerType": "touch",
            "isPrimary": True,
            "clientX": 400,
            "clientY": 300,
        },
    )
    stage.dispatch_event(
        "pointerup",
        {
            "pointerId": 2,
            "pointerType": "touch",
            "isPrimary": True,
            "button": 0,
            "clientX": 400,
            "clientY": 300,
        },
    )
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
        "document.querySelector('[data-ms-player]').dataset.state === 'paused'",
        timeout=10_000,
    )
    page.locator("[data-ms-gesture]").click()
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
    assert "Slide 1 forward asset" in page.locator(
        "[data-ms-error-message]"
    ).text_content()
    context.close()
