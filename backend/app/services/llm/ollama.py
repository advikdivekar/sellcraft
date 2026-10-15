import base64
import json
import time

import httpx

from ...config import get_settings
from ...errors import AppError
from .base import LLMProvider, LLMResult


class OllamaProvider(LLMProvider):
    name = "ollama"

    def __init__(self, base_url: str | None = None, model: str | None = None, timeout: float | None = None):
        s = get_settings()
        self.base_url = (base_url or s.ollama_base_url).rstrip("/")
        self.model = model or s.ollama_model
        self.timeout = timeout or s.ollama_timeout

    def health(self) -> dict:
        try:
            r = httpx.get(f"{self.base_url}/api/tags", timeout=3)
            r.raise_for_status()
        except httpx.HTTPError:
            return {"reachable": False, "model": self.model, "model_available": False,
                    "hint": f"Install Ollama (https://ollama.com) and run: ollama pull {self.model}"}
        names = {m.get("name", "") for m in r.json().get("models", [])}
        base = self.model.split(":")[0]
        available = self.model in names or (":" not in self.model and any(n.split(":")[0] == base for n in names))
        out = {"reachable": True, "model": self.model, "model_available": available}
        if not available:
            out["hint"] = f"Model not installed. Run: ollama pull {self.model}"
        return out

    def generate_json(self, system, user, schema, *, temperature=0.4, images=None) -> LLMResult:
        payload = {
            "model": self.model,
            "stream": False,
            "format": schema,
            "options": {"temperature": temperature},
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user, **({"images": [base64.b64encode(i).decode() for i in images]} if images else {})}],
        }
        t0 = time.monotonic()
        try:
            r = httpx.post(f"{self.base_url}/api/chat", json=payload, timeout=self.timeout)
        except httpx.ConnectError:
            raise AppError("llm_offline", f"Can't reach Ollama at {self.base_url}. Start it, then run: ollama pull {self.model}",
                           retryable=True, status=503)
        except httpx.TimeoutException:
            raise AppError("llm_timeout", "The language model took too long to respond. Try a smaller model or retry.",
                           retryable=True, status=504)
        if r.status_code == 404:
            raise AppError("llm_model_missing", f"Model '{self.model}' isn't installed. Run: ollama pull {self.model}",
                           status=503)
        if r.status_code >= 400:
            raise AppError("llm_error", f"The language model returned an error (HTTP {r.status_code}).",
                           retryable=True, status=502)
        body = r.json()
        content = (body.get("message") or {}).get("content", "")
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            raise AppError("llm_bad_json", "The model returned malformed JSON.", retryable=True, status=502)
        if not isinstance(data, dict):
            raise AppError("llm_bad_json", "The model returned an unexpected JSON shape.", retryable=True, status=502)
        usage = {"prompt_tokens": body.get("prompt_eval_count"), "completion_tokens": body.get("eval_count")}
        return LLMResult(data=data, model=self.model, latency_ms=int((time.monotonic() - t0) * 1000), usage=usage)
