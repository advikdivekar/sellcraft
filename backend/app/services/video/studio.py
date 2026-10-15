"""Turns raw phone photos into studio-style product imagery: background removal (rembg, an open-source
U2-Net model), mild tone enhancement, a designed backdrop per visual style, contact shadow and reflection.
Everything is deterministic image processing; nothing here invents product details."""
import colorsys
import logging
import threading
from dataclasses import dataclass, field

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
    """Return the product as a tight RGBA crop at the photo's FULL resolution, or None if no clean subject was found.
    The mask is predicted on a small copy (fast) and scaled up, so the product keeps all of its real pixels."""
    try:
        from rembg import remove
        work = img.convert("RGB")
        if max(work.size) > 3000:
            work.thumbnail((3000, 3000), Image.LANCZOS)
        small = work.copy()
        small.thumbnail((1400, 1400), Image.LANCZOS)
        with _lock:
            pred = remove(small, session=_get_session())
    except Exception:  # noqa: BLE001 - missing package, no network for the model download, etc.
        log.warning("background removal failed", exc_info=True)
        return None
    pred = _keep_main_subject(pred)
    alpha_small = pred.getchannel("A")
    cov = float((np.asarray(alpha_small) > 40).mean())
    if cov < 0.04 or cov > 0.96:  # nothing detected, or nothing was removed
        return None
    alpha = alpha_small.resize(work.size, Image.LANCZOS)
    out = work.convert("RGBA")
    out.putalpha(alpha)
    box = alpha.point(lambda v: 255 if v > 24 else 0).getbbox()
    if not box:
        return None
    pad = int(0.02 * max(out.size))
    box = (max(0, box[0] - pad), max(0, box[1] - pad), min(out.width, box[2] + pad), min(out.height, box[3] + pad))
    return out.crop(box)


def _keep_main_subject(rgba: Image.Image) -> Image.Image:
    """Drop faint smudges and stray blobs: keep the largest connected region (plus any region >= 15% of it)."""
    from scipy import ndimage
    a = np.asarray(rgba.getchannel("A"))
    labels, n = ndimage.label(a > 60)
    if n < 1:
        return rgba
    sizes = ndimage.sum(np.ones_like(a, dtype=np.float32), labels, index=range(1, n + 1))
    keep = [i + 1 for i, sz in enumerate(sizes) if sz >= 0.15 * sizes.max()]
    mask = np.isin(labels, keep)
    mask = ndimage.binary_dilation(mask, iterations=3)  # keep soft edge pixels next to the kept regions
    # push faint alpha (smudges, halos) to fully transparent and near-solid to opaque
    crisp = np.clip((a.astype(np.float32) - 50) / (215 - 50), 0, 1) * 255
    out = rgba.copy()
    out.putalpha(Image.fromarray((crisp * mask).astype(np.uint8)))
    return out


def _decontaminate_edges(rgb: np.ndarray, alpha: np.ndarray) -> np.ndarray:
    """Replace edge-pixel colours (which still carry the old background) with colours from just inside the subject."""
    from scipy import ndimage
    interior = ndimage.binary_erosion(alpha > 200, iterations=4).astype(np.float32)
    if interior.sum() < 100:
        return rgb
    w = ndimage.gaussian_filter(interior, 5) + 1e-4
    fill = np.stack([ndimage.gaussian_filter(rgb[..., c] * interior, 5) / w for c in range(3)], axis=-1)
    ring = ((alpha > 0) & (interior == 0))[..., None]
    return np.where(ring, fill, rgb)


_sr_cache: dict = {}
SR_URLS = {
    "fsrcnn": "https://github.com/Saafke/FSRCNN_Tensorflow/raw/master/models/FSRCNN_x2.pb",
    "espcn": "https://github.com/fannymonori/TF-ESPCN/raw/master/export/ESPCN_x2.pb",
    "edsr": "https://github.com/Saafke/EDSR_Tensorflow/raw/master/models/EDSR_x2.pb",
}


def _superres_model():
    """OpenCV dnn_superres network (x2). Downloads a small .pb once; None if unavailable (upscaling is then skipped)."""
    name = get_settings().superres_model.lower()
    if name not in SR_URLS:
        return None
    with _lock:
        if name in _sr_cache:
            return _sr_cache[name]
        model = None
        try:
            import cv2
            path = get_settings().db_path.parent / "models" / f"{name.upper()}_x2.pb"
            if not path.exists():
                import httpx
                path.parent.mkdir(parents=True, exist_ok=True)
                r = httpx.get(SR_URLS[name], follow_redirects=True, timeout=60)
                r.raise_for_status()
                tmp = path.with_suffix(".tmp")
                tmp.write_bytes(r.content)
                tmp.replace(path)
            model = cv2.dnn_superres.DnnSuperResImpl_create()
            model.readModel(str(path))
            model.setModel(name, 2)
        except Exception:  # noqa: BLE001
            log.warning("super-resolution model unavailable; skipping upscaling", exc_info=True)
        _sr_cache[name] = model
        return model


def refine(rgba: Image.Image, sharpness: float = 100.0) -> tuple[Image.Image, list[str]]:
    """Retouch the PRODUCT pixels (not just the backdrop): denoise, AI upscale, recover local contrast, fix colour
    cast and exposure, clean the edge halo, and sharpen in proportion to how soft the photo was. Never repaints
    or invents detail the way a generative model would, so labels, logos and shape stay true.
    Returns (image, what_was_done)."""
    import cv2
    done: list[str] = []
    im = rgba.convert("RGBA")
    if max(im.size) > 2000:  # keep processing time bounded on 12-MP phone photos
        im.thumbnail((2000, 2000), Image.LANCZOS)
    arr = np.asarray(im)
    a = arr[..., 3]
    bgr = cv2.cvtColor(arr[..., :3], cv2.COLOR_RGB2BGR)
    solid = a > 200

    # 1. denoise (strength follows the measured noise)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY).astype(np.float32)
    sigma = float(np.median(np.abs(cv2.Laplacian(gray, cv2.CV_32F)[solid])) / 0.6745) if solid.sum() > 200 else 0.0
    if sigma > 1.6:
        bgr = cv2.fastNlMeansDenoisingColored(bgr, None, float(np.clip(sigma * 0.7, 2.5, 7)), 4, 5, 15)
        done.append("reduced camera noise")

    # 2. AI super-resolution when the product has few pixels (x2, small neural net, runs on CPU)
    if max(im.size) < 1100:
        sr = _superres_model()
        if sr is not None:
            try:
                bgr = sr.upsample(bgr)
                a = np.asarray(Image.fromarray(a).resize((bgr.shape[1], bgr.shape[0]), Image.LANCZOS))
                done.append("upscaled 2× with a super-resolution network")
            except Exception:  # noqa: BLE001
                log.warning("super-resolution failed", exc_info=True)
    solid = a > 200

    # 3. local contrast (CLAHE on lightness only), blended so it never looks processed
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
    l_eq = cv2.createCLAHE(clipLimit=1.8, tileGridSize=(6, 6)).apply(lab[..., 0])
    lab[..., 0] = cv2.addWeighted(lab[..., 0], 0.55, l_eq, 0.45, 0)
    bgr = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    done.append("recovered local contrast")

    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB).astype(np.float32)
    # 4. colour cast + exposure, measured on the product only and capped
    if solid.sum() > 200:
        px = rgb[solid]
        mean = px.mean(axis=0)
        g = float(mean.mean())
        if float(np.abs(mean - g).max()) < 0.28 * g:  # strongly coloured products are not a cast
            gain = np.clip(g / np.maximum(mean, 1.0), 0.92, 1.08)
            if float(np.abs(gain - 1).max()) > 0.02:
                rgb = rgb * gain
                done.append("corrected colour cast")
        lo, hi = np.percentile(px.mean(axis=1), [1, 99])
        if hi - lo > 30:
            rgb = np.clip((rgb - lo * 0.5) * float(np.clip(235.0 / max(hi, 1.0), 0.9, 1.25)), 0, 255)
    rgb = _decontaminate_edges(rgb, a)

    out = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8))
    out = ImageEnhance.Contrast(out).enhance(1.03)
    out = ImageEnhance.Color(out).enhance(1.05)
    # 5. sharpen in proportion to softness (soft photos get more, sharp ones barely any)
    amount = 0.35 + 0.65 * float(np.clip((90 - sharpness) / 90, 0, 1))
    out = out.filter(ImageFilter.UnsharpMask(radius=1.6, percent=int(100 + 120 * amount), threshold=2)).convert("RGBA")
    if sharpness < 60:
        done.append("sharpened a soft photo")
    alpha = Image.fromarray(a).filter(ImageFilter.MinFilter(5)).filter(ImageFilter.GaussianBlur(1.1))
    out.putalpha(alpha)  # eroded + feathered edge: removes the light halo left by the old background
    return out, done


def enhance(rgba: Image.Image) -> Image.Image:
    return refine(rgba)[0]


@dataclass
class PhotoStats:
    """What we learned about a raw photo before processing it."""
    width: int
    height: int
    sharpness: float = 0.0
    brightness: float = 0.5  # of the product, 0..1
    saturation: float = 0.0
    hue: float = 0.0  # degrees
    coverage: float = 0.0  # product share of the frame, 0..1
    warnings: list[str] = field(default_factory=list)


def measure(img: Image.Image, cut: Image.Image | None) -> PhotoStats:
    st = PhotoStats(*img.size)
    g = np.asarray(img.convert("L").resize((min(img.width, 900), int(img.height * min(img.width, 900) / img.width))), np.float32)
    lap = g[1:-1, 1:-1] * 4 - g[:-2, 1:-1] - g[2:, 1:-1] - g[1:-1, :-2] - g[1:-1, 2:]
    st.sharpness = float(lap.var())
    if cut is not None:
        arr = np.asarray(cut.convert("RGBA").resize((160, int(160 * cut.height / cut.width))))
        solid = arr[..., 3] > 200
        if solid.sum() > 50:
            px = arr[..., :3][solid].astype(np.float32) / 255
            st.brightness = float((px @ np.array([0.299, 0.587, 0.114])).mean())
            hsv = np.array([colorsys.rgb_to_hsv(*p) for p in px[:: max(1, len(px) // 600)]])
            st.saturation = float(hsv[:, 1].mean())
            sat = hsv[hsv[:, 1] > 0.3]
            if len(sat):
                st.hue = float(np.degrees(np.arctan2(np.sin(sat[:, 0] * 2 * np.pi).mean(), np.cos(sat[:, 0] * 2 * np.pi).mean())) % 360)
        st.coverage = float((np.asarray(cut.getchannel("A")) > 40).mean() * cut.width * cut.height / (img.width * img.height))
    short = min(img.size)
    if short < 900:
        st.warnings.append(f"low resolution ({img.width}×{img.height}); the result may look soft")
    if st.sharpness < 25:
        st.warnings.append("looks blurry; hold the camera steady or tap to focus")
    if cut is not None and st.coverage < 0.12:
        st.warnings.append("the product is small in the frame; move closer")
    if cut is not None and st.brightness < 0.12:
        st.warnings.append("the product is very dark; add light if you can")
    return st


def adapt_palette(style: str, st: PhotoStats) -> tuple[tuple, str | None]:
    """Choose the backdrop from what the photo shows, so the product stands out against it."""
    top, bottom, spot, spot_k, refl, bokeh, block = SCENES.get(style, SCENES["minimal"])
    note = None
    shift = lambda c, d: tuple(int(np.clip(v + d, 0, 255)) for v in c)
    if style == "premium_studio" and st.brightness < 0.22:
        top, bottom, spot_k = shift(top, 34), shift(bottom, 40), spot_k + 0.14
        note = "Used a lighter backdrop so your dark product stands out."
    elif style == "minimal" and st.brightness > 0.82:
        top, bottom = shift(top, -26), shift(bottom, -30)
        note = "Used a slightly deeper backdrop so your light product stands out."
    elif style == "bold_colorful" and st.saturation > 0.35 and (min(abs(st.hue - 20), 360 - abs(st.hue - 20)) < 45):
        top, bottom, block = (24, 120, 255), (60, 220, 200), (255, 255, 255)
        note = "Used a cool blue backdrop so your warm-coloured product stands out."
    return (top, bottom, spot, spot_k, refl, bokeh, block), note


def catalog_image(prod: Image.Image, size: int = 1600) -> Image.Image:
    """Marketplace-style listing photo: product on pure white (RGB 255), centred, with a faint ground shadow."""
    canvas = Image.new("RGB", (size, size), (255, 255, 255))
    s = min(size * 0.84 / prod.width, size * 0.84 / prod.height)
    p = prod.resize((max(2, int(prod.width * s)), max(2, int(prod.height * s))), Image.LANCZOS)
    x, y = (size - p.width) // 2, (size - p.height) // 2
    sh = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse((x + p.width * 0.1, y + p.height - p.height * 0.03, x + p.width * 0.9, y + p.height + p.height * 0.05), fill=(0, 0, 0, 38))
    base = canvas.convert("RGBA")
    base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(size * 0.012)))
    base.alpha_composite(p, (x, y))
    return base.convert("RGB")


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


def scene(W: int, H: int, style: str, lay: Layout, palette: tuple | None = None) -> Image.Image:
    """Designed backdrop for a style, with a spotlight behind the product and a floor under it."""
    top, bottom, spot, spot_k, _, bokeh, block = palette or SCENES.get(style, SCENES["minimal"])
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
