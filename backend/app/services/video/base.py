from abc import ABC, abstractmethod
from pathlib import Path

SIZES = {"9:16": (1080, 1920), "4:5": (1080, 1350), "1:1": (1080, 1080), "16:9": (1920, 1080)}


def size_for(aspect: str) -> tuple[int, int]:
    return SIZES.get(aspect, SIZES["9:16"])


class ImageToVideoProvider(ABC):
    """Turns one product photo into a motion clip (no text, no audio; text and audio are added during assembly)."""

    name: str
    method: str  # label shown to the user: "animated_photo" | "ltx"

    @abstractmethod
    def available(self) -> bool: ...

    @abstractmethod
    def generate(self, image: Path, *, motion_prompt: str, style: str, duration: float,
                 size: tuple[int, int], out: Path) -> Path: ...
