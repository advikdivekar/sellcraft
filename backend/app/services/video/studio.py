"""Turns raw phone photos into studio-style product imagery: background removal (rembg, an open-source
U2-Net model), mild tone enhancement, a designed backdrop per visual style, contact shadow and reflection.
Everything is deterministic image processing; nothing here invents product details."""
import logging
import threading
from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

from ...config import get_settings

log = logging.getLogger("sellcraft.studio")
_lock = threading.RLock()
_session = None

# style -> (top rgb, bottom rgb, spotlight rgb, spot strength, reflection strength, bokeh?, colour block rgb or None)
SCENES = {
    "premium_studio": ((9, 9, 13), (30, 28, 38), (255, 238, 214), 0.42, 0.30, False, None),
    "minimal": ((246, 243, 238), (224, 218, 210), (255, 255, 255), 0.55, 0.12, False, None),
    "warm_cozy": ((70, 42, 26), (146, 90, 54), (255, 196, 134), 0.45, 0.0, True, None),
    "bold_colorful": ((255, 86, 56), (255, 176, 40), (255, 255, 255), 0.30, 0.18, False, (255, 255, 255)),
    "ugc": ((238, 231, 224), (208, 198, 192), (255, 250, 244), 0.40, 0.0, False, None),
}


def _get_session():
    global _session
    with _lock:
        if _session is None:
            from rembg import new_session
            _session = new_session(get_settings().cutout_model)
        return _session


def warmup() -> None:
    """Load the segmentation model ahead of the first request (downloads ~44 MB on first run)."""
    try:
        _get_session()
    except Exception:  # noqa: BLE001
        log.warning("background-removal model unavailable; photos will be framed instead of cut out")


def cutout(img: Image.Image) -> Image.Image | None:
    """Return the product as a tight RGBA crop, or None if no clean subject was found."""
    try:
        from rembg import remove
        work = img.convert("RGB")
        work.thumbnail((1400, 1400))
        with _lock:
            out = remove(work, session=_get_session())
    except Exception:  # noqa: BLE001 - missing package, no network for the model download, etc.
        log.warning("background removal failed", exc_info=True)
        return None
    alpha = out.getchannel("A")
    cov = float((np.asarray(alpha) > 40).mean())
    if cov < 0.04 or cov > 0.96:  # nothing detected, or nothing was removed
        return None
    box = alpha.point(lambda v: 255 if v > 24 else 0).getbbox()
    if not box:
        return None
    pad = int(0.02 * max(out.size))
    box = (max(0, box[0] - pad), max(0, box[1] - pad), min(out.width, box[2] + pad), min(out.height, box[3] + pad))
    return out.crop(box)


def enhance(rgba: Image.Image) -> Image.Image:
    """Gentle tone clean-up (contrast, colour, sharpness). Colours stay true to the product."""
    rgb, a = rgba.convert("RGB"), rgba.getchannel("A")
    rgb = ImageEnhance.Contrast(rgb).enhance(1.05)
    rgb = ImageEnhance.Color(rgb).enhance(1.07)
    rgb = ImageEnhance.Sharpness(rgb).enhance(1.25)
    out = rgb.convert("RGBA")
    out.putalpha(a)
    return out


def framed(img: Image.Image) -> Image.Image:
    """Fallback when background removal isn't possible: the whole photo as a rounded card."""
    im = img.convert("RGB")
    im.thumbnail((1400, 1400))
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, im.width - 1, im.height - 1), radius=int(0.05 * min(im.size)), fill=255)
    out = im.convert("RGBA")
    out.putalpha(mask)
    return out


@dataclass
class Layout:
    pw: int  # product width/height on the canvas
    ph: int
    cx: int  # product centre
    cy: int


def layout(W: int, H: int, prod: Image.Image, *, cy_frac: float = 0.36, w_frac: float = 0.78, h_frac: float = 0.50) -> Layout:
    box_w, box_h = int(W * w_frac), int(H * h_frac)
    s = min(box_w / prod.width, box_h / prod.height)
    return Layout(max(2, int(prod.width * s)), max(2, int(prod.height * s)), W // 2, int(H * cy_frac))


def product_layer(prod: Image.Image, lay: Layout, style: str) -> Image.Image:
    """Product + contact shadow + reflection on a transparent canvas whose centre IS the product centre,
    so FFmpeg can zoom it about its middle."""
    refl_k = SCENES.get(style, SCENES["minimal"])[4]
    p = prod.resize((lay.pw, lay.ph), Image.LANCZOS)
    LW, LH = int(lay.pw * 1.5), int(lay.ph * 2.0)
    layer = Image.new("RGBA", (LW, LH), (0, 0, 0, 0))
    px, py = (LW - lay.pw) // 2, (LH - lay.ph) // 2
    base_y = py + lay.ph
    # contact shadow
    sh = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    sw, shh = int(lay.pw * 0.85), max(10, int(lay.ph * 0.07))
    ImageDraw.Draw(sh).ellipse((LW // 2 - sw // 2, base_y - shh // 2, LW // 2 + sw // 2, base_y + shh), fill=(0, 0, 0, 120))
    layer.alpha_composite(sh.filter(ImageFilter.GaussianBlur(max(6, shh // 2))))
    # reflection (faded, flipped)
    if refl_k > 0:
        rh = int(lay.ph * 0.45)
        refl = p.transpose(Image.FLIP_TOP_BOTTOM).crop((0, 0, lay.pw, rh))
        fade = np.linspace(refl_k, 0, rh, dtype=np.float32)[:, None] * np.ones((1, lay.pw), np.float32)
        a = np.asarray(refl.getchannel("A"), np.float32) * fade
        refl.putalpha(Image.fromarray(a.astype(np.uint8)))
        layer.alpha_composite(refl, (px, base_y + 2))
    layer.alpha_composite(p, (px, py))
    return layer


def scene(W: int, H: int, style: str, lay: Layout) -> Image.Image:
    """Designed backdrop for a style, with a spotlight behind the product and a floor under it."""
    top, bottom, spot, spot_k, _, bokeh, block = SCENES.get(style, SCENES["minimal"])
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    t = (yy / H)[..., None]
    arr = np.asarray(top, np.float32) * (1 - t) + np.asarray(bottom, np.float32) * t
    d = np.sqrt(((xx - lay.cx) / (W * 0.75)) ** 2 + ((yy - lay.cy) / (H * 0.40)) ** 2)
    a = (np.clip(1 - d, 0, 1) ** 2 * spot_k)[..., None]
    arr = arr * (1 - a) + np.asarray(spot, np.float32) * a
    floor_y = lay.cy + lay.ph // 2
    f = np.clip((yy - floor_y) / (H * 0.10), 0, 1)[..., None]  # floor slightly darker/lighter under the product
    arr = arr * (1 - 0.10 * f) if style != "bold_colorful" else arr * (1 - 0.06 * f)
    dv = np.sqrt(((xx - W / 2) / (W * 0.80)) ** 2 + ((yy - H / 2) / (H * 0.80)) ** 2)  # vignette
    arr = arr * (1 - 0.30 * np.clip(dv - 0.35, 0, 1)[..., None])
    arr += np.random.default_rng(7).normal(0, 1.6, (H, W, 1)).astype(np.float32)  # grain hides gradient banding
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
    if block:
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        r = int(W * 0.46)
        ImageDraw.Draw(ov).ellipse((lay.cx - r, lay.cy - r, lay.cx + r, lay.cy + r), fill=block + (46,))
        img.alpha_composite(ov)
    if bokeh:
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dr, rng = ImageDraw.Draw(ov), np.random.default_rng(11)
        for _ in range(16):
            x, y, r = int(rng.uniform(0, W)), int(rng.uniform(0, H * 0.7)), int(rng.uniform(26, 78))
            dr.ellipse((x - r, y - r, x + r, y + r), fill=(255, 214, 160, int(rng.uniform(30, 70))))
        img.alpha_composite(ov.filter(ImageFilter.GaussianBlur(9)))
    return img.convert("RGB")


def sweep_png(W: int, H: int, path) -> int:
    """A soft slanted light streak that FFmpeg slides across the frame for a premium sheen.
    Returns the PNG width (the streak is skewed, so it needs extra width to avoid clipped edges)."""
    SW = int(W * 0.30)
    slant = 0.26
    CW = SW + int(H * slant)
    yy, xx = np.mgrid[0:H, 0:CW].astype(np.float32)
    u = (xx - yy * slant - SW / 2) / (SW / 2)
    a = np.clip(1 - np.abs(u), 0, 1) ** 2 * 0.20 * np.clip(np.sin(np.pi * (yy / H)) * 1.6, 0, 1)
    arr = np.full((H, CW, 4), 255, np.uint8)
    arr[..., 3] = (a * 255).astype(np.uint8)
    Image.fromarray(arr, "RGBA").save(path)
    return CW
