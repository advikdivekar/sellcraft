from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from collections.abc import Callable
from pathlib import Path

SIZES = {"9:16": (1080, 1920), "4:5": (1080, 1350), "1:1": (1080, 1080), "16:9": (1920, 1080)}
FPS = 30


def size_for(aspect: str) -> tuple[int, int]:
    return SIZES.get(aspect, SIZES["9:16"])


@dataclass
class ClipResult:
    clip: Path
    method: str  # "studio_cutout" | "animated_photo" | "ltx"
    images: list[tuple[str, Path]] = field(default_factory=list)  # (asset kind, file): studio_image / catalog_image / cutout_image
    notes: list[str] = field(default_factory=list)  # honest notes, e.g. "Background removal failed for photo 2"


class ImageToVideoProvider(ABC):
    """Turns product photos into a motion clip (no text, no audio; text and audio are added during assembly)."""

    name: str

    @abstractmethod
    def available(self) -> bool: ...

    @abstractmethod
    def generate(self, images: list[Path], *, style: str, duration: float, size: tuple[int, int],
                 out_dir: Path, on_progress: Callable[[float], None] | None = None) -> ClipResult: ...
