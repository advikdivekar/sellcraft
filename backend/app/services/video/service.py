import shutil
from pathlib import Path

from ... import db
from ...config import get_settings
from ...errors import AppError
from ...schemas import CopyOutput, GenerationJob
from . import ffmpeg
from .assemble import assemble
from .base import ImageToVideoProvider, size_for
from .cards import clean_text, render_card
from .base import ClipResult
from .deck import Slide, build as build_deck
from .provider import StudioAdProvider


def get_provider() -> ImageToVideoProvider:
    name = get_settings().video_provider.lower()
    if name in ("fallback", "", "animated_photo"):
        return StudioAdProvider()
    raise AppError("video_provider_unavailable",
                   f"Video provider '{name}' isn't available. Set VIDEO_PROVIDER=fallback to use the animated-photo ad.", status=503)


def job_dir(job_id: str) -> Path:
    d = get_settings().output_path / job_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def _source_images(job: GenerationJob) -> list[Path]:
    paths = []
    for aid in job.product.image_asset_ids:
        row = db.get_asset_row(aid)
        if row is None:
            raise AppError("image_missing", "A product photo is no longer available. Please upload it again.", status=404)
        paths.append(Path(row["path"]))
    return paths


def render_clip(job: GenerationJob, on_progress=None) -> ClipResult:
    """Stage: generating_video. Studio-enhances the photos and renders the motion clip (no text yet)."""
    provider = get_provider()
    if not provider.available():
        raise AppError("ffmpeg_missing", "FFmpeg isn't installed. Install it (brew install ffmpeg) and retry.", status=503)
    return provider.generate(_source_images(job), style=job.settings.visual_style.value,
                             duration=float(job.settings.duration_seconds), size=size_for(job.settings.aspect_ratio),
                             out_dir=job_dir(job.id), on_progress=on_progress)


def overlay_plan(copy: CopyOutput, product_name: str) -> dict:
    """What appears on screen. Only seller-facing copy they can edit; the feature comes from verified facts."""
    return {
        "hook": clean_text(copy.video_hook or copy.ad_headline),
        "feature": clean_text(copy.key_features[0]) if copy.key_features else "",
        "name": clean_text(copy.product_title or product_name),
        "cta": clean_text(copy.call_to_action),
    }


def render_final(job: GenerationJob, clip: Path, *, audio: Path | None = None) -> tuple[Path, ffmpeg.Probe]:
    """Stage: assembling_video. Adds timed text cards (+ optional audio) and verifies the export."""
    copy = job.copy_output
    if copy is None:
        raise AppError("no_copy", "There's no copy to put on the video yet.", status=409)
    D = float(job.settings.duration_seconds)
    size = size_for(job.settings.aspect_ratio)
    style = job.settings.visual_style.value
    plan = overlay_plan(copy, job.product.name)
    d = job_dir(job.id)
    cards = []
    if plan["hook"]:
        cards.append((render_card([("title", plan["hook"])], style, size[0], d / "card_hook.png"), 0.25, 2.0, 0.745))
    if plan["feature"]:
        cards.append((render_card([("body", plan["feature"])], style, size[0], d / "card_feature.png"), 6.0, 8.0, 0.745))
    blocks = [("title", plan["name"])] + ([("pill", plan["cta"])] if plan["cta"] else [])
    cards.append((render_card(blocks, style, size[0], d / "card_cta.png"), 8.0, D, 0.745))
    out = d / f"final-{db.new_id()[:8]}.mp4"
    assemble(clip, cards, duration=D, size=size, out=out, audio=audio)
    try:
        probe = ffmpeg.validate(out, target=D, size=size)
    except AppError:
        out.unlink(missing_ok=True)
        raise
    return out, probe


def clear_outputs(job_id: str, *, kinds: tuple[str, ...]) -> None:
    for row in db.list_asset_rows(job_id, kinds):
        Path(row["path"]).unlink(missing_ok=True)
        db.delete_asset(row["id"])


def remove_job_dir(job_id: str) -> None:
    shutil.rmtree(get_settings().output_path / job_id, ignore_errors=True)


def render_deck(job: GenerationJob) -> tuple[list[Slide], list[str]]:
    """Stage: deck. Lays the refined product images on designed slides using the (editable) copy."""
    from PIL import Image
    copy = job.copy_output
    if copy is None:
        raise AppError("no_copy", "There's no copy to build the image deck from yet.", status=409)
    rows = db.list_asset_rows(job.id, ("product_src",))
    products = []
    for r in sorted(rows, key=lambda r: Path(r["path"]).name):  # product-0.png, product-1.png, ... = upload order
        with Image.open(r["path"]) as im:
            products.append(im.convert("RGBA"))
    if not products:
        raise AppError("deck_inputs_missing", "The refined product images are missing. Use Try again to rebuild them.", retryable=True, status=409)
    d = job_dir(job.id)
    for old in d.glob("deck-*.jpg"):
        old.unlink(missing_ok=True)
    return build_deck(products, style=job.settings.visual_style.value, copy=copy, product_name=job.product.name,
                      brand=job.product.brand_name, out_dir=d)
