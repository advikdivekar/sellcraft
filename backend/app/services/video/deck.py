"""The image deck: a carousel of consistent 4:5 slides built from the REFINED product images.
Slides: hero, benefits (only facts the seller gave), close-up detail, extra angles, call to action.
Nothing here generates new product imagery; it lays the real, refined product on designed slides."""
import re
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from . import cards, studio

W, H = 1080, 1350


@dataclass
class Slide:
    kind: str  # hero | benefits | detail | angle | cta
    path: Path


def _luma(c) -> float:
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def _ink(palette) -> tuple[tuple, tuple]:
    """(text colour, muted text colour) that read on this backdrop."""
    dark = _luma(palette[1]) < 140
    return ((255, 255, 255), (222, 218, 212)) if dark else ((26, 24, 22), (92, 86, 80))


def _wrap(draw, text, font, max_w):
    return cards._wrap(draw, text, font, max_w)


def _text_block(draw, text, y, *, font_path, max_w, max_lines, start, floor, fill, cx=W // 2, line_gap=1.18):
    """Centered, auto-sized text. Returns the y below the block."""
    font, lines = cards._fit(draw, cards.clean_text(text), font_path, max_w, max_lines, start, floor)
    for ln in lines:
        draw.text((cx - draw.textlength(ln, font=font) / 2, y), ln, font=font, fill=fill)
        y += int(font.size * line_gap)
    return y


def _base(prod: Image.Image, style: str, palette, *, cy: float, w_frac: float, h_frac: float):
    lay = studio.layout(W, H, prod, cy_frac=cy, w_frac=w_frac, h_frac=h_frac)
    bg = studio.scene(W, H, style, lay, palette).convert("RGBA")
    layer = studio.product_layer(prod, lay, style)
    bg.alpha_composite(layer, (lay.cx - layer.width // 2, lay.cy - layer.height // 2))
    return bg


def hero(prod, style, palette, name, tagline) -> Image.Image:
    img = _base(prod, style, palette, cy=0.43, w_frac=0.82, h_frac=0.62)
    d = ImageDraw.Draw(img)
    ink, muted = _ink(palette)
    y = _text_block(d, name, 1020, font_path=cards._font_path(), max_w=880, max_lines=2, start=76, floor=48, fill=ink)
    if tagline:
        _text_block(d, tagline, y + 10, font_path=cards.regular_font_path(), max_w=840, max_lines=2, start=38, floor=28, fill=muted)
    return img.convert("RGB")


def benefits(prod, style, palette, heading, items, accent) -> Image.Image:
    n = min(len(items), 4)
    card_h, gap, bottom = 118, 16, 84
    cards_top = H - bottom - (n * card_h + (n - 1) * gap)
    head_y = cards_top - 96
    box_h = head_y - 40 - 70  # the product gets whatever room the list leaves, so short lists feel balanced
    lay = studio.layout(W, H, prod, cy_frac=(70 + box_h / 2) / H, w_frac=0.62, h_frac=box_h / H * 0.92)
    bg = studio.scene(W, H, style, lay, palette).convert("RGBA")
    layer = studio.product_layer(prod, lay, style)
    bg.alpha_composite(layer, (lay.cx - layer.width // 2, lay.cy - layer.height // 2))
    img, d = bg, ImageDraw.Draw(bg, "RGBA")
    ink, _ = _ink(palette)
    hf = ImageFont.truetype(str(cards._font_path()), 54)
    d.text((W // 2 - d.textlength(heading, font=hf) / 2, head_y), heading, font=hf, fill=ink)
    for k, text in enumerate(items[:n]):
        y = cards_top + k * (card_h + gap)
        d.rounded_rectangle((70, y, W - 70, y + card_h), radius=30, fill=(255, 255, 255, 236))
        cx, cy = 70 + 58, y + card_h // 2
        d.ellipse((cx - 30, cy - 30, cx + 30, cy + 30), fill=accent + (255,))
        d.line([(cx - 13, cy + 1), (cx - 4, cy + 11), (cx + 14, cy - 10)], fill=(255, 255, 255), width=7, joint="curve")
        font, lines = cards._fit(d, cards.clean_text(text), cards.regular_font_path(), W - 70 * 2 - 130 - 30, 2, 40, 28)
        ty = cy - (len(lines) * int(font.size * 1.2)) // 2
        for ln in lines:
            d.text((70 + 112, ty), ln, font=font, fill=(32, 28, 26))
            ty += int(font.size * 1.2)
    return img.convert("RGB")


def detail(prod, style, palette, caption, accent) -> Image.Image | None:
    """A close-up crop from the refined high-resolution product. Skipped if there aren't enough real pixels."""
    pw, ph = prod.size
    cw, ch = int(pw * 0.62), int(ph * 0.46)
    if cw < 520 or ch < 520:
        return None
    x0, y0 = (pw - cw) // 2, int(ph * 0.16)
    crop = prod.crop((x0, y0, x0 + cw, y0 + ch))
    frame_w, frame_h = 900, 960
    s = max(frame_w / crop.width, frame_h / crop.height)
    crop = crop.resize((int(crop.width * s), int(crop.height * s)), Image.LANCZOS)
    lay = studio.Layout(frame_w, frame_h, W // 2, 560)
    img = studio.scene(W, H, style, lay, palette).convert("RGBA")
    mask = Image.new("L", (frame_w, frame_h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, frame_w - 1, frame_h - 1), radius=54, fill=255)
    card = Image.new("RGBA", (frame_w, frame_h), (255, 255, 255, 255))
    card.alpha_composite(crop, ((frame_w - crop.width) // 2, (frame_h - crop.height) // 2))
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle((90 + 0, 80 + 18, 90 + frame_w, 80 + frame_h + 18), radius=54, fill=(0, 0, 0, 90))
    img.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(22)))
    img.paste(card, (90, 80), mask)
    d = ImageDraw.Draw(img, "RGBA")
    font = ImageFont.truetype(str(cards._font_path()), 42)
    text = cards.clean_text(caption) or "Close-up"
    tw = d.textlength(text, font=font)
    px0, py0 = (W - tw) / 2 - 38, 1112
    d.rounded_rectangle((px0, py0, px0 + tw + 76, py0 + 86), radius=43, fill=accent + (255,))
    d.text((px0 + 38, py0 + 17), text, font=font, fill=(255, 255, 255))
    return img.convert("RGB")


def angle(prod, style, palette) -> Image.Image:
    return _base(prod, style, palette, cy=0.45, w_frac=0.84, h_frac=0.70).convert("RGB")


def cta(prod, style, palette, name, cta_text, brand, accent) -> Image.Image:
    img = _base(prod, style, palette, cy=0.33, w_frac=0.62, h_frac=0.42)
    d = ImageDraw.Draw(img, "RGBA")
    ink, muted = _ink(palette)
    y = _text_block(d, name, 800, font_path=cards._font_path(), max_w=880, max_lines=2, start=74, floor=46, fill=ink)
    if cta_text:
        font, lines = cards._fit(d, cards.clean_text(cta_text), cards._font_path(), 760, 2, 48, 34)
        w = max(d.textlength(l, font=font) for l in lines) + 90
        h = len(lines) * int(font.size * 1.2) + 46
        x0, y0 = (W - w) / 2, y + 34
        d.rounded_rectangle((x0, y0, x0 + w, y0 + h), radius=h // 2, fill=accent + (255,))
        ty = y0 + 23
        for ln in lines:
            d.text((W / 2 - d.textlength(ln, font=font) / 2, ty), ln, font=font, fill=(255, 255, 255))
            ty += int(font.size * 1.2)
        y = y0 + h
    if brand:
        _text_block(d, brand, 1230, font_path=cards.regular_font_path(), max_w=840, max_lines=1, start=40, floor=28, fill=muted)
    return img.convert("RGB")


def benefit_items(copy) -> tuple[str, list[str]]:
    """Only things the seller supplied or confirmed: verified benefits first, else the feature bullets."""
    src, heading = (copy.benefits, "Why you’ll like it") if len([b for b in copy.benefits if b.strip()]) >= 2 else (copy.key_features, "Highlights")
    items = [re.sub(r"\s+", " ", x).strip(" -•") for x in src if x and x.strip()]
    return heading, items


def build(products: list[Image.Image], *, style: str, copy, product_name: str, brand: str | None, out_dir: Path) -> tuple[list[Slide], list[str]]:
    """products[0] is the hero. Returns (slides in order, notes about skipped slides)."""
    notes: list[str] = []
    out_dir.mkdir(parents=True, exist_ok=True)
    stats = studio.measure(products[0].convert("RGB"), products[0])
    palette, _ = studio.adapt_palette(style, stats)
    accent = cards.PALETTE.get(style, cards.PALETTE["minimal"])[2]
    slides: list[tuple[str, Image.Image]] = []
    slides.append(("hero", hero(products[0], style, palette, copy.product_title or product_name, copy.ad_headline)))
    heading, items = benefit_items(copy)
    if len(items) >= 2:
        slides.append(("benefits", benefits(products[0], style, palette, heading, items, accent)))
    else:
        notes.append("Add at least two features or verified benefits to get a benefits slide.")
    label = items[0] if items and len(items[0]) <= 30 else "Close-up"  # a long sentence doesn't belong in a small label
    det = detail(products[0], style, palette, label, accent)
    if det is not None:
        slides.append(("detail", det))
    else:
        notes.append("Skipped the close-up slide: the photo doesn't have enough pixels on the product. A closer photo would fix that.")
    for extra in products[1:]:
        slides.append(("angle", angle(extra, style, studio.adapt_palette(style, studio.measure(extra.convert("RGB"), extra))[0])))
    slides.append(("cta", cta(products[0], style, palette, copy.product_title or product_name, copy.call_to_action, brand, accent)))
    out = []
    for i, (kind, img) in enumerate(slides, start=1):
        p = out_dir / f"deck-{i:02d}-{kind}.jpg"
        img.save(p, quality=93)
        out.append(Slide(kind, p))
    return out, notes
