import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image, ImageOps

from . import ffmpeg, studio
from .base import FPS, ClipResult, ImageToVideoProvider

log = logging.getLogger("sellcraft.studio")
XF = 0.4  # crossfade between shots (seconds)
MARGIN = 54  # extra backdrop around the frame so it can drift for parallax


def plan_shots(n: int) -> list[tuple[int, str]]:
    """(photo index, camera move) per shot. Always >= 4 shots, starts and ends on the hero photo."""
    if n == 1:
        return list(zip([0, 0, 0, 0], ["push", "detail", "pull", "hero"]))
    order = list(range(n)) + [0]
    while len(order) < 4:
        order.insert(-1, len(order) % n)
    mids = ["detail", "pull", "sway"]
    moves = ["push"] + [mids[i % 3] for i in range(len(order) - 2)] + ["hero"]
    return list(zip(order, moves))


# move -> (zoom start, zoom end, dx expr (uses d), dy as fraction of product height, light sweep?)
MOVES = {
    "push": (1.00, 1.10, "0", 0.0, True),
    "detail": (1.30, 1.42, "0", 0.10, False),
    "pull": (1.22, 1.04, "0", 0.0, False),
    "sway": (1.04, 1.08, "22*sin(2*PI*t/{d})", 0.0, False),
    "hero": (1.00, 1.06, "0", 0.0, True),
}


class StudioAdProvider(ImageToVideoProvider):
    """Studio-style ad from the seller's own photos: background removed, product re-lit on a designed
    backdrop with shadow/reflection, then animated with multi-shot camera moves in FFmpeg.
    This is image processing, not generative video, and the UI labels it that way."""

    name = "ffmpeg-studio"

    def available(self) -> bool:
        return ffmpeg.available()

    def _prep(self, i: int, path: Path, style: str, W: int, H: int, out_dir: Path):
        with Image.open(path) as raw:
            img = ImageOps.exif_transpose(raw).convert("RGB")
        cut = studio.cutout(img)
        prod = studio.enhance(cut) if cut is not None else studio.framed(img)
        lay = studio.layout(W, H, prod)
        layer = studio.product_layer(prod, lay, style)
        m = MARGIN
        bg = studio.scene(W + 2 * m, H + 2 * m, style, studio.Layout(lay.pw, lay.ph, lay.cx + m, lay.cy + m))
        layer_p, bg_p = out_dir / f"layer{i}.png", out_dir / f"bg{i}.png"
        layer.save(layer_p)
        bg.save(bg_p)
        # a still product photo (4:5, Instagram feed shape) on the same backdrop
        SW, SH = 1080, 1350
        slay = studio.layout(SW, SH, prod, cy_frac=0.46, w_frac=0.80, h_frac=0.70)
        still = studio.scene(SW, SH, style, slay).convert("RGBA")
        sl = studio.product_layer(prod, slay, style)
        still.alpha_composite(sl, (slay.cx - sl.width // 2, slay.cy - sl.height // 2))
        still_p = out_dir / f"studio-{i}.jpg"
        still.convert("RGB").save(still_p, quality=93)
        return {"layer": layer_p, "bg": bg_p, "lay": lay, "LW": layer.width, "LH": layer.height,
                "cutout": cut is not None, "still": still_p}

    def _shot(self, k: int, prep: dict, move: str, d: float, W: int, H: int, sweep: Path, sweep_w: int, out: Path) -> Path:
        z0, z1, dx, dyf, use_sweep = MOVES[move]
        lay, m = prep["lay"], MARGIN
        z = f"({z0}+({z1 - z0})*t/{d:.3f})"
        dxe = dx.format(d=f"{d:.3f}")
        dy = f"{dyf * lay.ph:.1f}"
        bx = f"{m}+{-30 if k % 2 == 0 else 30}*t/{d:.3f}"  # backdrop drifts slower than the product: parallax
        by = f"{m}+{14}*t/{d:.3f}"
        SWW = sweep_w
        g = (f"[0:v]crop={W}:{H}:x='{bx}':y='{by}'[bg];"
             f"[1:v]format=rgba,scale=w='trunc({prep['LW']}*{z}/2)*2':h='trunc({prep['LH']}*{z}/2)*2':eval=frame:flags=bicubic[fg];"
             f"[bg][fg]overlay=x='{lay.cx}-w/2+({dxe})':y='{lay.cy}-h/2+{dy}':eval=frame[a];")
        if use_sweep:
            g += f"[a][2:v]overlay=x='-{SWW}+({W}+{SWW})*t/{d:.3f}':y=0:eval=frame[b];[b]"
        else:
            g += "[a]"
        g += "scale=out_range=tv,format=yuv420p[v]"
        args = []
        for src in (prep["bg"], prep["layer"], sweep):
            args += ["-loop", "1", "-framerate", str(FPS), "-t", f"{d:.3f}", "-i", str(src)]
        ffmpeg.run([*args, "-filter_complex", g, "-map", "[v]", "-r", str(FPS), "-c:v", "libx264",
                    "-preset", "veryfast", "-crf", "14", "-pix_fmt", "yuv420p", str(out)])
        return out

    def generate(self, images: list[Path], *, style: str, duration: float, size: tuple[int, int],
                 out_dir: Path) -> ClipResult:
        W, H = size
        out_dir.mkdir(parents=True, exist_ok=True)
        with ThreadPoolExecutor(max_workers=3) as pool:
            preps = list(pool.map(lambda a: self._prep(a[0], a[1], style, W, H, out_dir), enumerate(images)))
        sweep = out_dir / "sweep.png"
        sweep_w = studio.sweep_png(W, H, sweep)
        shots = plan_shots(len(images))
        k = len(shots)
        d = (duration + (k - 1) * XF) / k
        with ThreadPoolExecutor(max_workers=3) as pool:
            files = list(pool.map(
                lambda a: self._shot(a[0], preps[a[1][0]], a[1][1], d, W, H, sweep, sweep_w, out_dir / f"shot{a[0]}.mp4"),
                enumerate(shots)))
        clip = out_dir / "clip.mp4"
        parts, last = [], "0:v"
        for i in range(1, k):
            parts.append(f"[{last}][{i}:v]xfade=transition=fade:duration={XF}:offset={i * (d - XF):.3f}[x{i}]")
            last = f"x{i}"
        args = []
        for f in files:
            args += ["-i", str(f)]
        ffmpeg.run([*args, "-filter_complex", ";".join(parts), "-map", f"[{last}]", "-r", str(FPS), "-c:v", "libx264",
                    "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", "-t", f"{duration}", str(clip)])
        for f in files:
            f.unlink(missing_ok=True)
        notes = [f"Background removal wasn't possible for photo {i + 1}, so it was shown as a framed photo."
                 for i, p in enumerate(preps) if not p["cutout"]]
        method = "studio_cutout" if preps[0]["cutout"] else "animated_photo"
        return ClipResult(clip=clip, method=method, stills=[p["still"] for p in preps], notes=notes)
