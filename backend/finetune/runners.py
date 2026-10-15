"""Model providers for the fine-tuning toolkit, all behind the app's LLMProvider interface:
  ollama   local models (Gemma baselines, or your fine-tuned model after `ollama create`)
  openai   any OpenAI-compatible chat endpoint (an open-weight teacher on a host of your choice, or Tinker's beta
           OpenAI-compatible endpoint for trained checkpoints)
  tinker   Tinker's native SDK sampling for base models (written from the docs; not yet run against a live key)"""
import json
import os
import re
import time

import httpx

from app.errors import AppError
from app.services.llm.base import LLMProvider, LLMResult
from app.services.llm.ollama import OllamaProvider

def load_env() -> None:
    """Make backend/.env values (like TINKER_API_KEY) visible to these scripts. Never prints them."""
    from pathlib import Path
    f = Path(__file__).resolve().parents[1] / ".env"
    if f.exists():
        for line in f.read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                if v.strip() and k.strip() not in os.environ:
                    os.environ[k.strip()] = v.strip().strip("\"'")


TINKER_OAI = "https://tinker.thinkingmachines.dev/services/tinker-prod/oai/api/v1"


def schema_skeleton(schema: dict):
    """A compact example of the JSON shape (type names as placeholders). Hosts that can't enforce a schema need to be TOLD
    the exact field names, otherwise the model improvises and omits required fields."""
    t = schema.get("type")
    if t == "object":
        return {k: schema_skeleton(v) for k, v in (schema.get("properties") or {}).items()}
    if t == "array":
        return [schema_skeleton(schema.get("items") or {"type": "string"})]
    return "string"


def shape_instruction(schema: dict) -> str:
    return ("\n\nReply with ONE JSON object with exactly this shape and these keys (replace each \"string\" with real text; "
            "use [] or \"\" when you have nothing to say, never null):\n" + json.dumps(schema_skeleton(schema)))


def extract_json(text: str) -> dict:
    """Pull a JSON object out of model text: strips reasoning tags and markdown fences, tolerates chatter around it."""
    text = re.sub(r"<think>.*?</think>", "", text or "", flags=re.S).strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.S)
    try:
        v = json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, flags=re.S)
        if not m:
            raise AppError("llm_bad_json", "The model returned no JSON.", retryable=True, status=502)
        try:
            v = json.loads(m.group(0))
        except json.JSONDecodeError:
            raise AppError("llm_bad_json", "The model returned malformed JSON.", retryable=True, status=502)
    if not isinstance(v, dict):
        raise AppError("llm_bad_json", "The model returned an unexpected JSON shape.", retryable=True, status=502)
    return v


class OpenAICompatProvider(LLMProvider):
    name = "openai"

    def __init__(self, base_url: str, model: str, api_key: str = "", timeout: float = 240, json_mode: str = "json_schema",
                 max_tokens: int = 2048, client: httpx.Client | None = None):
        self.base_url, self.model, self.api_key = base_url.rstrip("/"), model, api_key
        self.timeout, self.json_mode, self.max_tokens = timeout, json_mode, max_tokens
        self.client = client or httpx.Client(timeout=timeout)

    def health(self) -> dict:
        return {"reachable": True, "model": self.model}

    def _post(self, body: dict) -> httpx.Response:
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        try:
            return self.client.post(f"{self.base_url}/chat/completions", json=body, headers=headers)
        except httpx.TimeoutException:
            raise AppError("llm_timeout", "The model took too long to respond.", retryable=True, status=504)
        except httpx.HTTPError:
            raise AppError("llm_offline", f"Can't reach {self.base_url}.", retryable=True, status=503)

    def generate_json(self, system, user, schema, *, temperature=0.4, images=None) -> LLMResult:
        mode = self.json_mode
        t0 = time.monotonic()
        for attempt in range(3):
            body = {"model": self.model, "temperature": temperature, "max_tokens": self.max_tokens,
                    "messages": [{"role": "system", "content": system},
                                 {"role": "user", "content": user + ("" if mode != "none" else shape_instruction(schema))}]}
            if mode == "json_schema":
                body["response_format"] = {"type": "json_schema", "json_schema": {"name": "kit_part", "schema": schema}}
            elif mode == "json_object":
                body["response_format"] = {"type": "json_object"}
            r = self._post(body)
            if r.status_code == 400 and mode != "none" and attempt < 2:
                mode = "json_object" if mode == "json_schema" else "none"  # host doesn't support that response_format
                continue
            break
        if r.status_code in (401, 403):
            raise AppError("llm_auth", "The API key was rejected.", status=502)
        if r.status_code == 429:
            raise AppError("llm_rate_limited", "Rate limited by the model host.", retryable=True, status=429)
        if r.status_code >= 400:
            raise AppError("llm_error", f"The model host returned HTTP {r.status_code}.", retryable=True, status=502)
        body = r.json()
        content = ((body.get("choices") or [{}])[0].get("message") or {}).get("content", "")
        usage = body.get("usage") or {}
        return LLMResult(data=extract_json(content), model=self.model, latency_ms=int((time.monotonic() - t0) * 1000),
                         usage={"prompt_tokens": usage.get("prompt_tokens"), "completion_tokens": usage.get("completion_tokens")})


class TinkerNativeProvider(LLMProvider):
    """Samples a Tinker-hosted base model or checkpoint with the native SDK (needs `pip install tinker` + TINKER_API_KEY)."""
    name = "tinker"

    def __init__(self, base_model: str, max_tokens: int = 4096):
        self.model, self.max_tokens = base_model, max_tokens
        self._sampler = self._tok = None

    def health(self) -> dict:
        return {"reachable": bool(os.getenv("TINKER_API_KEY")), "model": self.model}

    def _init(self):
        if self._sampler is None:
            import tinker
            svc = tinker.ServiceClient()
            self._sampler = svc.create_sampling_client(base_model=self.model)
            self._tok = svc.create_lora_training_client(base_model=self.model, rank=8).get_tokenizer()

    def generate_json(self, system, user, schema, *, temperature=0.4, images=None) -> LLMResult:
        import asyncio
        from tinker import types
        self._init()
        t0 = time.monotonic()
        msgs = [{"role": "system", "content": system}, {"role": "user", "content": user + shape_instruction(schema)}]
        try:  # hybrid-reasoning models (Qwen3 family) otherwise spend your tokens "thinking" first
            text = self._tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True, enable_thinking=False)
        except TypeError:
            text = self._tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
        prompt = types.ModelInput.from_ints(self._tok.encode(text))
        params = types.SamplingParams(max_tokens=self.max_tokens, temperature=temperature)
        res = asyncio.run(self._sampler.sample_async(prompt=prompt, num_samples=1, sampling_params=params))
        toks = res.sequences[0].tokens
        return LLMResult(data=extract_json(self._tok.decode(toks)), model=self.model, latency_ms=int((time.monotonic() - t0) * 1000),
                         usage={"prompt_tokens": len(prompt.to_ints()) if hasattr(prompt, "to_ints") else None, "completion_tokens": len(toks)})


def add_provider_args(ap):
    ap.add_argument("--provider", choices=["ollama", "openai", "tinker"], default="ollama")
    ap.add_argument("--model", required=True, help="ollama tag, hosted model name, or Tinker base model / checkpoint")
    ap.add_argument("--base-url", default="", help="OpenAI-compatible base URL (use 'tinker' for Tinker's beta endpoint)")
    ap.add_argument("--api-key-env", default="TEACHER_API_KEY", help="env var holding the API key (openai provider)")
    ap.add_argument("--json-mode", choices=["json_schema", "json_object", "none"], default="json_schema")


def provider_from_args(a) -> LLMProvider:
    load_env()
    if a.provider == "ollama":
        return OllamaProvider(model=a.model, timeout=600)
    if a.provider == "tinker":
        return TinkerNativeProvider(a.model)
    base = TINKER_OAI if a.base_url == "tinker" else a.base_url
    if not base:
        raise SystemExit("--base-url is required for the openai provider")
    key = os.getenv("TINKER_API_KEY" if a.base_url == "tinker" else a.api_key_env, "")
    return OpenAICompatProvider(base, a.model, key, json_mode=a.json_mode)
