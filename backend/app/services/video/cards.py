"""Text cards rendered with Pillow (no FFmpeg drawtext / fontconfig needed, no text in FFmpeg commands)."""
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from ...config import BASE_DIR
from ...errors import AppError

FONT_CANDIDATES = [
    BASE_DIR / "assets" / "fonts" / "bold.ttf",
    Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
    Path("/Library/Fonts/Arial Bold.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    Path("/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf"),
    Path("C:/Windows/Fonts/arialbd.ttf"),
]
# style -> (card fill rgba, text colour, accent colour)
PALETTE = {
    "premium_studio": ((12, 12, 14, 205), (255, 255, 255), (214, 178, 106)),
    "ugc": ((20, 16, 14, 190), (255, 255, 255), (255, 120, 80)),
    "minimal": ((250, 247, 242, 230), (28, 25, 23), (194, 65, 12)),
    "warm_cozy": ((52, 31, 18, 215), (255, 240, 224), (240, 160, 90)),
    "bold_colorful": ((255, 255, 255, 235), (22, 22, 22), (214, 58, 29)),
}


def _font_path() -> Path:
    for p in FONT_CANDIDATES:
        if p.is_file():
            return p
    raise AppError("font_missing", "No bold font was found for text overlays. Add one at backend/assets/fonts/bold.ttf.", status=500)


def clean_text(s: str) -> str:
    s = re.sub(r"[\u0000-\u001f\u007f\ufe0f\u200d]", " ", s or "")
    s = "".join(ch for ch in s if ord(ch) <= 0xFFFF and not (0x2190 <= ord(ch) <= 0x2BFF))  # no emoji/symbols
    return re.sub(r"\s+", " ", s).strip()


def _wrap(draw, text, font, max_w) -> list[str]:
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if draw.textlength(trial, font=font) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def _fit(draw, text, path, max_w, max_lines, start, floor):
    for size in range(start, floor - 1, -4):
        font = ImageFont.truetype(str(path), size)
        lines = _wrap(draw, text, font, max_w)
        if len(lines) <= max_lines and all(draw.textlength(l, font=font) <= max_w for l in lines):
            return font, lines
    font = ImageFont.truetype(str(path), floor)
    lines = _wrap(draw, text, font, max_w)[:max_lines]
    if lines:
        lines[-1] = lines[-1].rstrip(" .,") + "…"
    return font, lines


def render_card(blocks: list[tuple[str, str]], style: str, frame_w: int, out: Path) -> Path:
    """blocks: [("title"|"body"|"pill", text)]. Returns a transparent PNG card sized to its content."""
    fill, fg, accent = PALETTE.get(style, PALETTE["minimal"])
    path = _font_path()
    max_w = int(frame_w * 0.80)
    pad_x, pad_y, gap = 52, 44, 26
    probe = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    laid = []
    for kind, raw in blocks:
        text = clean_text(raw)
        if not text:
            continue
        start, floor, lines_max = {"title": (92, 52, 3), "body": (68, 44, 3), "pill": (52, 38, 2)}[kind]
        inner_w = max_w - (2 * 30 if kind == "pill" else 0)
        font, lines = _fit(probe, text, path, inner_w, lines_max, start, floor)
        lh = int(font.size * 1.22)
        w = max(probe.textlength(l, font=font) for l in lines)
        laid.append((kind, font, lines, lh, w))
    if not laid:
        raise AppError("empty_card", "There is no text to show on this part of the video.")
    content_w = max(w + (60 if k == "pill" else 0) for k, _, _, _, w in laid)
    content_h = sum(len(l) * lh + (28 if k == "pill" else 0) for k, _, l, lh, _ in laid) + gap * (len(laid) - 1)
    W, H = int(content_w + 2 * pad_x), int(content_h + 2 * pad_y)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, W - 1, H - 1), radius=44, fill=fill)
    y = pad_y
    for kind, font, lines, lh, w in laid:
        if kind == "pill":
            pw, ph = int(w + 60), len(lines) * lh + 28
            x0 = (W - pw) // 2
            d.rounded_rectangle((x0, y, x0 + pw, y + ph), radius=ph // 2, fill=accent + (255,))
            ty, color = y + 14, (255, 255, 255)
        else:
            ty, color = y, fg if kind == "title" else fg
        for line in lines:
            d.text(((W - d.textlength(line, font=font)) / 2, ty), line, font=font, fill=color)
            ty += lh
        y += (len(lines) * lh + (28 if kind == "pill" else 0)) + gap
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    return out
