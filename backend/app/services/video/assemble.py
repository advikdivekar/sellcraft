from pathlib import Path

from . import ffmpeg
from .fallback import FPS

FADE = 0.35


def assemble(clip: Path, cards: list[tuple[Path, float, float, float]], *, duration: float, size: tuple[int, int],
             out: Path, audio: Path | None = None) -> Path:
    """Overlay timed text cards (png, start, end, y-centre fraction) onto a motion clip, optionally mix audio.
    Output: H.264 / yuv420p / faststart (plays on iPhone Safari), AAC audio only when audio is supplied."""
    W, H = size
    args = ["-i", str(clip)]
    for png, *_ in cards:
        args += ["-loop", "1", "-framerate", str(FPS), "-t", str(duration), "-i", str(png)]
    parts, last = [], "0:v"
    for i, (_, start, end, cy) in enumerate(cards, start=1):
        fade_out = f",fade=t=out:st={max(start, end - FADE):.2f}:d={FADE}:alpha=1" if end < duration - 0.01 else ""
        parts.append(f"[{i}:v]format=rgba,fade=t=in:st={start:.2f}:d={FADE}:alpha=1{fade_out}[c{i}]")
        parts.append(f"[{last}][c{i}]overlay=x='(W-w)/2':y='{int(H * cy)}-h/2':eval=init[o{i}]")
        last = f"o{i}"
    if not cards:
        parts.append("[0:v]null[o0]")
        last = "o0"
    parts.append(f"[{last}]format=yuv420p[v]")
    args += ["-filter_complex", ";".join(parts), "-map", "[v]"]
    if audio:
        args += ["-i", str(audio), "-map", f"{len(cards) + 1}:a", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11,apad",
                 "-c:a", "aac", "-b:a", "128k"]
    args += ["-t", str(duration), "-r", str(FPS), "-c:v", "libx264", "-preset", "medium", "-crf", "20",
             "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)]
    ffmpeg.run(args)
    return out
