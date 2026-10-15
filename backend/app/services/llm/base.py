from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class LLMResult:
    data: dict
    model: str
    latency_ms: int = 0
    usage: dict = field(default_factory=dict)  # prompt_tokens / completion_tokens when known


class LLMProvider(ABC):
    name: str

    @abstractmethod
    def health(self) -> dict: ...

    @abstractmethod
    def generate_json(self, system: str, user: str, schema: dict, *, temperature: float = 0.4) -> LLMResult:
        """Return parsed JSON that conforms (best effort) to `schema`. Raises AppError on failure."""
