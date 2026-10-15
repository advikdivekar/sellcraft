from pathlib import Path

from . import ffmpeg
from .base import ImageToVideoProvider

FPS = 30
# style -> (tint colour, tint opacity, zoom start, zoom end, sway px)
STYLE = {
    "premium_studio": ("0x0b0b0d", 0.45, 1.00, 1.07, 0),
    "ugc": ("0x1a1410", 0.30, 1.03, 1.06, 14),
    "minimal": ("0xf3efe8", 0.35, 1.00, 1.04, 0),
    "warm_cozy": ("0x3b2314", 0.40, 1.07, 1.00, 0),
    "bold_colorful": ("0xd63a1d", 0.40, 1.00, 1.10, 10),
}


class AnimatedPhotoFallbackProvider(ImageToVideoProvider):
    """Honest fallback: the seller's own photo, framed on a blurred canvas, with a slow zoom/pan.
    Not AI-generated footage, and it is labelled that way everywhere."""

    name = "ffmpeg-animated-photo"
    method = "animated_photo"

    def available(self) -> bool:
        return ffmpeg.available()

    def generate(self, image: Path, *, motion_prompt: str, style: str, duration: float,
                 size: tuple[int, int], out: Path) -> Path:
        from PIL import Image
        W, H = size
        with Image.open(image) as im:
            iw, ih = im.size
        # Fit the product inside a safe box in the upper part of the frame (text sits below it).
        box_w, box_h = int(W * 0.86), int(H * 0.52)
        scale = min(box_w / iw, box_h / ih)
        fw, fh = max(2, int(iw * scale)), max(2, int(ih * scale))
        cy = int(H * 0.37)
        tint, alpha, z0, z1, sway = STYLE.get(style, STYLE["minimal"])
        z = f"({z0}+({z1}-{z0})*t/{duration})"
        sway_x = f"+{sway}*sin(2*PI*t/5)" if sway else ""
        graph = (
            f"[0:v]split=2[a][b];"
            f"[a]scale={W // 4}:{H // 4}:force_original_aspect_ratio=increase,crop={W // 4}:{H // 4},"
            f"boxblur=12:3,scale={W}:{H},drawbox=x=0:y=0:w=iw:h=ih:color={tint}@{alpha}:t=fill[bg];"
            f"[b]scale=w='{fw}*{z}':h='{fh}*{z}':eval=frame:flags=bicubic[fg];"
            f"[bg][fg]overlay=x='(W-w)/2{sway_x}':y='{cy}-h/2':eval=frame,format=yuv420p[v]"
        )
        ffmpeg.run([
            "-loop", "1", "-framerate", str(FPS), "-t", str(duration), "-i", str(image),
            "-filter_complex", graph, "-map", "[v]", "-r", str(FPS),
            "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", str(out),
        ])
        return out
