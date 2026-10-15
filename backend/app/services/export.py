import html
import io
import json
import re
import zipfile
from pathlib import Path

from ..schemas import CopyOutput, Platform
from .prompts import PLATFORM_FIELDS

_LABEL = lambda k: k.replace("_", " ").capitalize()


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "product"


def _fmt(v) -> str:
    return "\n".join(f"- {x}" for x in v) if isinstance(v, list) else str(v)


def listing_text(copy: CopyOutput, platforms: list[Platform]) -> str:
    """Plain-text version of the whole kit, ready to paste."""
    out = ["# Listing"]
    for k in ("product_title", "short_description", "full_description", "key_features", "benefits", "keywords", "tags",
              "seo_title", "meta_description"):
        out.append(f"\n## {_LABEL(k)}\n{_fmt(getattr(copy, k))}")
    out.append("\n# Social")
    for k in ("social_caption", "hashtags", "ad_headline", "call_to_action"):
        out.append(f"\n## {_LABEL(k)}\n{_fmt(getattr(copy, k))}")
    for p in platforms:
        out.append(f"\n# {p.value.capitalize()}")
        for f in PLATFORM_FIELDS[p]:
            out.append(f"\n## {_LABEL(f)}\n{_fmt(copy.platform_outputs.get(p.value, {}).get(f, ''))}")
    out.append("\n# Video brief")
    for k in ("video_hook", "voiceover_script", "video_generation_prompt"):
        out.append(f"\n## {_LABEL(k)}\n{_fmt(getattr(copy, k))}")
    return "\n".join(out) + "\n"


def listing_html(copy: CopyOutput) -> str:
    """Safe HTML body for a store listing. Every value is escaped."""
    e = html.escape
    parts = [f"<p>{e(p)}</p>" for p in re.split(r"\n{2,}|\n", copy.full_description.strip()) if p.strip()]
    if copy.key_features:
        parts.append("<ul>" + "".join(f"<li>{e(f)}</li>" for f in copy.key_features) + "</ul>")
    return "".join(parts)


def kit_zip(*, name: str, copy: CopyOutput, platforms: list[Platform], files: list[tuple[str, Path]]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("listing.txt", listing_text(copy, platforms))
        z.writestr("listing.json", json.dumps(copy.model_dump(), indent=2, ensure_ascii=False))
        for arcname, path in files:
            if path.is_file():
                z.write(path, arcname, compress_type=zipfile.ZIP_STORED)
    return buf.getvalue()
