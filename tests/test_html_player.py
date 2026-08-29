import base64
import hashlib
import json
import shutil
from pathlib import Path
from typing import cast

import pytest
from bs4 import BeautifulSoup
from click.testing import CliRunner
from pydantic import ValidationError

from manim_slides.__main__ import cli
from manim_slides.config import PresentationConfig, SlideConfig, SlideType
from manim_slides.convert import Converter, HtmlPlayer, RevealJS


def read_manifest(output: Path) -> dict:
    soup = BeautifulSoup(output.read_text(encoding="utf-8"), "html.parser")
    node = soup.select_one("[data-ms-manifest]")
    assert node is not None
    return json.loads(node.text)


def payloads(output: Path) -> dict[str, tuple[str, bytes]]:
    soup = BeautifulSoup(output.read_text(encoding="utf-8"), "html.parser")
    return {
        cast(str, node["data-ms-asset"]): (
            cast(str, node["data-mime"]),
            base64.b64decode(node.text.strip(), validate=True),
        )
        for node in soup.select("script[data-ms-asset]")
    }


def test_converter_lookup() -> None:
    assert Converter.from_string("html-player") is HtmlPlayer


def test_cli_selection_and_show_config(slides_folder: Path) -> None:
    runner = CliRunner()
    shown = runner.invoke(cli, ["-S", "convert", "--to=html-player", "--show-config"])
    assert shown.exit_code == 0
    assert "one_file: False" in shown.output
    assert "background_size: 'contain'" in shown.output

    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            [
                "-S",
                "convert",
                "BasicSlide",
                "player.html",
                "--folder",
                str(slides_folder),
                "--to=html-player",
                "--one-file",
            ],
        )
        assert result.exit_code == 0, result.output
        assert Path("player.html").is_file()
        assert not Path("player_assets").exists()


def test_custom_reveal_template_is_rejected() -> None:
    with pytest.raises(ValidationError) as error:
        HtmlPlayer.model_validate(
            {"presentation_configs": [], "template": "revealjs.html"}
        )
    assert error.value.errors()[0]["loc"] == ("template",)


def test_manifest_is_deterministic_for_multiple_scenes(
    tmp_path: Path, presentation_config: PresentationConfig
) -> None:
    outputs = [tmp_path / "first.html", tmp_path / "second.html"]
    for output in outputs:
        HtmlPlayer(
            presentation_configs=[presentation_config, presentation_config],
            one_file=True,
            title="A deterministic deck",
        ).convert_to(output)
    manifests = [read_manifest(output) for output in outputs]
    assert manifests[0] == manifests[1]
    assert len(manifests[0]["presentations"]) == 2
    assert len(manifests[0]["slides"]) == 2 * len(presentation_config.slides)
    assert manifests[0]["version"] == 1


def test_asset_backed_copies_forward_reverse_and_local_runtime(
    tmp_path: Path, presentation_config: PresentationConfig
) -> None:
    output = tmp_path / "deck.html"
    HtmlPlayer(presentation_configs=[presentation_config]).convert_to(output)
    manifest = read_manifest(output)
    assets = tmp_path / "deck_assets"
    assert assets.is_dir()
    assert {"player-core.js", "player.js", "player.css"} <= {
        path.name for path in assets.iterdir()
    }
    references = {
        slide[role]["url"]
        for slide in manifest["slides"]
        for role in ("forward", "reverse")
    }
    assert all(url.startswith("deck_assets/media-") for url in references)
    assert all((tmp_path / Path(url)).is_file() for url in references)
    assert all(
        slide["forward"]["id"] != slide["reverse"]["id"] for slide in manifest["slides"]
    )
    content = output.read_text(encoding="utf-8")
    assert "https://" not in content
    assert "http://" not in content


def test_collision_safe_asset_names(
    tmp_path: Path, presentation_config: PresentationConfig
) -> None:
    dirs = [tmp_path / "one", tmp_path / "two"]
    for directory in dirs:
        directory.mkdir()
    sources = [presentation_config.slides[0].file, presentation_config.slides[-1].file]
    same_names = []
    for directory, source in zip(dirs, sources, strict=True):
        destination = directory / "clip.mp4"
        shutil.copyfile(source, destination)
        same_names.append(destination)
    slides = [
        SlideConfig(file=path, rev_file=path, type=SlideType.Video)
        for path in same_names
    ]
    output = tmp_path / "collision.html"
    HtmlPlayer(presentation_configs=[PresentationConfig(slides=slides)]).convert_to(
        output
    )
    names = [slide["forward"]["url"] for slide in read_manifest(output)["slides"]]
    assert len(set(names)) == 2
    assert all("clip.mp4" not in name for name in names)


def test_portable_payloads_are_unique_exact_and_inert(
    tmp_path: Path, presentation_config: PresentationConfig
) -> None:
    output = tmp_path / "portable.html"
    HtmlPlayer(presentation_configs=[presentation_config], one_file=True).convert_to(
        output
    )
    manifest = read_manifest(output)
    embedded = payloads(output)
    referenced = {
        slide[role]["id"]
        for slide in manifest["slides"]
        for role in ("forward", "reverse")
    }
    assert set(embedded) == referenced
    assert all(mime == "video/mp4" for mime, _ in embedded.values())
    expected = {
        hashlib.sha256(path.read_bytes()).hexdigest()[:16]: path.read_bytes()
        for slide in presentation_config.slides
        for path in (slide.file, slide.rev_file)
    }
    for asset_id, (_, data) in embedded.items():
        assert data == expected[asset_id.removeprefix("asset-")]
    content = output.read_text(encoding="utf-8")
    assert "data:video" not in content
    assert "https://" not in content
    assert "http://" not in content
    assert "deck_assets" not in content


def test_metadata_and_hostile_text_are_safe(
    tmp_path: Path, presentation_config: PresentationConfig
) -> None:
    hostile = '</script><script>globalThis.hostile = "yes"</script>&\u2028'
    slide = presentation_config.slides[0].model_copy(
        update={
            "auto_next": True,
            "direction": "vertical",
            "loop": True,
            "notes": hostile,
            "playback_rate": 1.5,
            "reversed_playback_rate": 0.75,
        }
    )
    config = PresentationConfig(
        slides=[slide],
        resolution=(640, 360),
        background_color="#123456",
    )
    output = tmp_path / "hostile.html"
    HtmlPlayer(presentation_configs=[config], one_file=True, title=hostile).convert_to(
        output
    )
    manifest = read_manifest(output)
    got = manifest["slides"][0]
    assert got["autoNext"] and got["loop"]
    assert got["direction"] == "vertical"
    assert got["notes"] == hostile
    assert got["playbackRate"] == 1.5
    assert got["reversedPlaybackRate"] == 0.75
    assert got["resolution"] == [640, 360]
    content = output.read_text(encoding="utf-8")
    assert "</script><script>globalThis.hostile" not in content
    assert "&lt;/script&gt;&lt;script&gt;globalThis.hostile" in content
    assert "\\u003c/script\\u003e" in content


def test_image_slide_uses_one_first_class_asset(tmp_path: Path) -> None:
    image = tmp_path / "still.png"
    from PIL import Image

    Image.new("RGB", (8, 8), "purple").save(image)
    slide = SlideConfig(file=image, rev_file=image, type=SlideType.Image, notes="Still")
    output = tmp_path / "image.html"
    HtmlPlayer(
        presentation_configs=[PresentationConfig(slides=[slide])], one_file=True
    ).convert_to(output)
    manifest = read_manifest(output)
    got = manifest["slides"][0]
    assert got["type"] == "image"
    assert got["forward"] == got["reverse"]
    assert len(payloads(output)) == 1
    assert next(iter(payloads(output).values()))[0] == "image/png"


def test_missing_and_corrupt_assets_fail_with_slide_and_role(tmp_path: Path) -> None:
    corrupt = tmp_path / "corrupt.mp4"
    corrupt.write_bytes(b"not a video")
    slide = SlideConfig(file=corrupt, rev_file=corrupt)
    with pytest.raises(ValueError, match=r"scene-1-slide-1.*forward.*corrupt\.mp4"):
        HtmlPlayer(
            presentation_configs=[PresentationConfig(slides=[slide])]
        ).convert_to(tmp_path / "corrupt.html")

    missing = tmp_path / "missing.mp4"
    shutil.copyfile(Path("tests/data/video.mp4"), missing)
    missing_slide = SlideConfig(file=missing, rev_file=missing)
    missing.unlink()
    with pytest.raises(ValueError, match=r"scene-1-slide-1.*forward.*missing\.mp4"):
        HtmlPlayer(
            presentation_configs=[PresentationConfig(slides=[missing_slide])]
        ).convert_to(tmp_path / "missing.html")


def test_revealjs_compatibility_still_copies_only_forward_assets(
    tmp_path: Path, presentation_config: PresentationConfig
) -> None:
    output = tmp_path / "reveal.html"
    RevealJS(presentation_configs=[presentation_config]).convert_to(output)
    assert len(list((tmp_path / "reveal_assets").iterdir())) == len(
        presentation_config.slides
    )
