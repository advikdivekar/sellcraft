import json
import logging
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from ...errors import AppError

log = logging.getLogger("sellcraft.ffmpeg")


def available() -> bool:
    return bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))


def run(args: list[str], *, timeout: int = 240) -> None:
    """Run ffmpeg with an argument list (never a shell string). Filter graphs contain only numbers
    and labels; user text is rendered to images beforehand, so nothing user-supplied is interpreted."""
    if not available():
        raise AppError("ffmpeg_missing", "FFmpeg isn't installed. Install it (brew install ffmpeg) and retry.", status=503)
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
    except subprocess.TimeoutExpired:
        raise AppError("video_timeout", "Rendering the video took too long. Please retry.", retryable=True, status=504)
    if r.returncode != 0:
        log.error("ffmpeg failed (%s): %s", r.returncode, r.stderr[-800:])
        raise AppError("video_render_failed", "The video couldn't be rendered. Please retry.", retryable=True, status=500)


@dataclass
class Probe:
    duration: float
    video_codec: str
    pix_fmt: str
    width: int
    height: int
    has_audio: bool


def probe(path: Path) -> Probe:
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,codec_name,width,height,pix_fmt:format=duration",
             "-of", "json", str(path)], capture_output=True, text=True, timeout=30, check=True)
        d = json.loads(r.stdout)
        v = next(s for s in d["streams"] if s["codec_type"] == "video")
        return Probe(float(d["format"]["duration"]), v["codec_name"], v.get("pix_fmt", ""), int(v["width"]),
                     int(v["height"]), any(s["codec_type"] == "audio" for s in d["streams"]))
    except (subprocess.SubprocessError, KeyError, StopIteration, ValueError, json.JSONDecodeError, OSError):
        raise AppError("video_invalid", "The rendered video couldn't be read back, so it was rejected.", retryable=True, status=500)


def validate(path: Path, *, target: float, size: tuple[int, int], tolerance: float = 0.5) -> Probe:
    p = probe(path)
    if abs(p.duration - target) > tolerance:
        raise AppError("video_bad_duration", f"The video came out {p.duration:.1f}s instead of {target:.0f}s.", retryable=True, status=500)
    if p.video_codec != "h264" or p.pix_fmt != "yuv420p" or (p.width, p.height) != size:
        raise AppError("video_bad_format", "The video wasn't exported in the expected format.", retryable=True, status=500)
    return p
