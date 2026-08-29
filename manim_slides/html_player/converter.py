import base64
import hashlib
import html
import json
import mimetypes
import os
import shutil
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any, TextIO
from urllib.parse import quote

import av
from av.error import FFmpegError
from PIL import Image

from ..config import PresentationConfig, SlideType


@dataclass(frozen=True)
class PlayerAsset:
    id: str
    source: Path
    mime_type: str
    kind: str
    filename: str


@dataclass(frozen=True)
class PlayerBuildResult:
    mode: str
    asset_count: int
    output_size: int


def _resource_text(name: str) -> str:
    return (
        resources.files("manim_slides.html_player")
        .joinpath(name)
        .read_text(encoding="utf-8")
    )


def _safe_json(value: object) -> str:
    """Serialize inert JSON without allowing an input to close its script tag."""
    return (
        json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        .replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def _color_css(value: object) -> str:
    return str(value)


def _validate_media(path: Path, kind: str, slide_id: str, role: str) -> None:
    try:
        if kind == "image":
            with Image.open(path) as image:
                image.verify()
        else:
            with av.open(str(path)) as container:
                if not container.streams.video:
                    raise ValueError("it contains no video stream")
                next(container.decode(video=0))
    except (OSError, StopIteration, ValueError, FFmpegError) as error:
        raise ValueError(
            f"Slide '{slide_id}' has an unreadable {role} {kind} asset "
            f"'{path}': {error}"
        ) from error


def _asset_for(
    path: Path,
    kind: str,
    slide_id: str,
    role: str,
    assets_by_key: dict[tuple[str, str], PlayerAsset],
) -> PlayerAsset:
    mime_type = mimetypes.guess_type(path.name)[0]
    expected_prefix = f"{kind}/"
    if mime_type is None or not mime_type.startswith(expected_prefix):
        raise ValueError(
            f"Slide '{slide_id}' has unsupported {role} asset '{path}'; "
            f"expected a recognized {kind} MIME type."
        )

    _validate_media(path, kind, slide_id, role)
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    hexdigest = digest.hexdigest()
    key = (hexdigest, mime_type)
    if key in assets_by_key:
        return assets_by_key[key]

    suffix = path.suffix.lower()
    asset = PlayerAsset(
        id=f"asset-{hexdigest[:16]}",
        source=path,
        mime_type=mime_type,
        kind=kind,
        filename=f"media-{hexdigest[:16]}{suffix}",
    )
    assets_by_key[key] = asset
    return asset


def _asset_reference(asset: PlayerAsset, one_file: bool) -> dict[str, str]:
    reference = {
        "id": asset.id,
        "kind": asset.kind,
        "mimeType": asset.mime_type,
        "storage": "inline" if one_file else "file",
    }
    if not one_file:
        reference["url"] = quote(asset.filename, safe="")
    return reference


def _plan(
    presentation_configs: list[PresentationConfig],
    title: str,
    background_size: str,
    one_file: bool,
) -> tuple[dict[str, Any], list[PlayerAsset]]:
    assets_by_key: dict[tuple[str, str], PlayerAsset] = {}
    slides: list[dict[str, object]] = []
    presentations: list[dict[str, object]] = []

    for scene_index, presentation in enumerate(presentation_configs):
        start = len(slides)
        for slide_index, slide in enumerate(presentation.slides):
            slide_id = f"scene-{scene_index + 1}-slide-{slide_index + 1}"
            kind = "image" if slide.type == SlideType.Image else "video"
            forward = _asset_for(
                slide.file, kind, slide_id, "forward", assets_by_key
            )
            reverse = (
                forward
                if kind == "image"
                else _asset_for(
                    slide.rev_file,
                    kind,
                    slide_id,
                    "reverse",
                    assets_by_key,
                )
            )
            slides.append(
                {
                    "autoNext": slide.auto_next,
                    "backgroundColor": _color_css(presentation.background_color),
                    "direction": slide.direction,
                    "forward": _asset_reference(forward, one_file),
                    "id": slide_id,
                    "loop": slide.loop,
                    "notes": slide.notes,
                    "playbackRate": slide.playback_rate,
                    "resolution": list(presentation.resolution),
                    "reverse": _asset_reference(reverse, one_file),
                    "reversedPlaybackRate": slide.reversed_playback_rate,
                    "sceneIndex": scene_index,
                    "slideIndex": slide_index,
                    "type": kind,
                }
            )
        presentations.append(
            {
                "backgroundColor": _color_css(presentation.background_color),
                "count": len(presentation.slides),
                "id": f"scene-{scene_index + 1}",
                "resolution": list(presentation.resolution),
                "start": start,
            }
        )

    manifest: dict[str, Any] = {
        "backgroundSize": background_size,
        "presentations": presentations,
        "slides": slides,
        "title": title,
        "version": 1,
    }
    return manifest, sorted(assets_by_key.values(), key=lambda asset: asset.id)


def _write_base64(stream: TextIO, source: Path) -> None:
    remainder = b""
    with source.open("rb") as media:
        for chunk in iter(lambda: media.read(3 * 1024 * 1024), b""):
            data = remainder + chunk
            complete = len(data) - (len(data) % 3)
            if complete:
                stream.write(base64.b64encode(data[:complete]).decode("ascii"))
            remainder = data[complete:]
    if remainder:
        stream.write(base64.b64encode(remainder).decode("ascii"))


def build_html_player(
    presentation_configs: list[PresentationConfig],
    dest: Path,
    assets_dir_template: str,
    one_file: bool,
    title: str,
    background_size: str,
) -> PlayerBuildResult:
    """Build an asset-backed or single-file first-party HTML presentation."""
    if not presentation_configs:
        raise ValueError("At least one presentation configuration is required.")

    manifest, assets = _plan(
        presentation_configs, title, background_size, one_file
    )
    dirname = dest.parent
    assets_dir = Path(
        assets_dir_template.format(
            dirname=dirname, basename=dest.stem, ext=dest.suffix
        )
    )
    full_assets_dir = dirname / assets_dir
    template = _resource_text("player.html")
    core = _resource_text("player-core.js")
    runtime = _resource_text("player.js")
    styles = _resource_text("player.css")

    if one_file:
        style_tag = f"<style>\n{styles}\n</style>"
        script_tags = f"<script>\n{core}\n</script>\n<script>\n{runtime}\n</script>"
    else:
        full_assets_dir.mkdir(parents=True, exist_ok=True)
        for asset in assets:
            shutil.copyfile(asset.source, full_assets_dir / asset.filename)
        (full_assets_dir / "player-core.js").write_text(core, encoding="utf-8")
        (full_assets_dir / "player.js").write_text(runtime, encoding="utf-8")
        (full_assets_dir / "player.css").write_text(styles, encoding="utf-8")
        try:
            relative_assets_dir = Path(os.path.relpath(full_assets_dir, dirname))
        except ValueError as error:
            raise ValueError(
                "The HTML file and its assets directory must be on the same drive."
            ) from error
        prefix = quote(relative_assets_dir.as_posix().rstrip("/"), safe="/")
        for slide in manifest["slides"]:
            for role in ("forward", "reverse"):
                reference = slide[role]
                reference["url"] = f"{prefix}/{reference['url']}"
        style_tag = f'<link rel="stylesheet" href="{prefix}/player.css">'
        script_tags = (
            f'<script src="{prefix}/player-core.js"></script>\n'
            f'<script src="{prefix}/player.js"></script>'
        )

    rendered = (
        template.replace("@@TITLE@@", html.escape(title, quote=True))
        .replace("@@STYLES@@", style_tag)
        .replace("@@MANIFEST@@", _safe_json(manifest))
        .replace("@@SCRIPTS@@", script_tags)
    )
    before_payloads, after_payloads = rendered.split("@@PAYLOADS@@", 1)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w", encoding="utf-8", newline="\n") as output:
        output.write(before_payloads)
        if one_file:
            for asset in assets:
                output.write(
                    f'<script type="application/octet-stream" data-ms-asset="{asset.id}" '
                    f'data-mime="{html.escape(asset.mime_type, quote=True)}">'
                )
                _write_base64(output, asset.source)
                output.write("</script>\n")
        output.write(after_payloads)

    return PlayerBuildResult(
        mode="portable" if one_file else "asset-backed",
        asset_count=len(assets),
        output_size=dest.stat().st_size,
    )
