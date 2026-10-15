import logging
import re
from dataclasses import dataclass, field

from pydantic import ValidationError

from ..config import get_settings
from ..errors import AppError
from ..schemas import CopyOutput, CreativeSettings, Platform, ProductInput, Tone
from . import prompts
from .llm.base import LLMProvider
from .llm.demo import demo_copy, demo_section
from .llm.ollama import OllamaProvider

log = logging.getLogger("sellcraft.copy")

REQUIRED_NONEMPTY = ("product_title", "short_description", "full_description", "social_caption",
                     "video_hook", "voiceover_script")


@dataclass
class CopyResult:
    copy: CopyOutput
    source: str  # "ollama:<model>" | "demo"
    usage: dict = field(default_factory=dict)


def _as_list(v) -> list[str]:
    if v is None:
        return []
    if isinstance(v, str):
        return [p.strip(" -•\t") for p in re.split(r"[\n;]|(?<=\.)\s", v) if p.strip(" -•\t")]
    return [str(x).strip() for x in v if str(x).strip()]


def _as_str(v) -> str:
    if v is None:
        return ""
    if isinstance(v, (list, tuple)):
        return " ".join(str(x) for x in v)
    return str(v).strip()


def normalize(data: dict, kinds: dict[str, str] | None = None) -> dict:
    """Coerce common small-model slips (list vs string) before Pydantic validation."""
    out = {}
    for k, v in data.items():
        kind = (kinds or prompts.CORE_FIELDS).get(k)
        if kind == "list":
            out[k] = _as_list(v)
        elif kind == "str":
            out[k] = _as_str(v)
        elif k == "platform_outputs" and isinstance(v, dict):
            out[k] = {}
            for pname, fields in v.items():
                try:
                    spec = prompts.PLATFORM_FIELDS[Platform(pname)]
                except ValueError:
                    continue
                fields = fields if isinstance(fields, dict) else {}
                out[k][pname] = {f: (_as_list(fields.get(f)) if t == "list" else _as_str(fields.get(f)))
                                 for f, t in spec.items()}
        else:
            out[k] = v
    return out


def _validate(data: dict, platforms: list[Platform]) -> CopyOutput:
    cleaned = normalize(data)
    cleaned.setdefault("platform_outputs", {})
    try:
        copy = CopyOutput.model_validate(cleaned)
    except ValidationError as e:
        raise AppError("llm_invalid_output", f"The model's output didn't match the expected format: {e.error_count()} problems.",
                       retryable=True, status=502)
    if re.search(r"\{[A-Za-z_]+\}|\[[A-Za-z_ ]+\]", copy.model_dump_json()):
        raise AppError("llm_placeholder_output", "The model left template placeholders in its output.",
                       retryable=True, status=502)
    empty = [f for f in REQUIRED_NONEMPTY if not getattr(copy, f).strip()]
    empty += [f"platform_outputs.{p.value}" for p in platforms if not any(copy.platform_outputs.get(p.value, {}).values())]
    if empty:
        raise AppError("llm_incomplete_output", "The model's output was missing: " + ", ".join(empty),
                       retryable=True, status=502)
    return copy


def forbidden_hits(copy: CopyOutput, words: list[str]) -> list[str]:
    if not words:
        return []
    text = copy.model_dump_json().lower()
    return [w for w in words if re.search(rf"(?<!\w){re.escape(w.lower())}(?!\w)", text)]


class CopyService:
    def __init__(self, llm: LLMProvider | None = None):
        self.demo = get_settings().demo_mode and llm is None
        self.llm = llm or (None if self.demo else OllamaProvider())

    def _call(self, system: str, user: str, schema: dict):
        """One call plus a single repair retry on malformed/invalid output."""
        try:
            return self.llm.generate_json(system, user, schema)
        except AppError as e:
            if e.code not in ("llm_bad_json",):
                raise
            log.warning("llm returned bad json; retrying once")
            return self.llm.generate_json(system, user + "\n\nYour previous reply was not valid JSON. Reply with valid JSON only.", schema)

    def generate(self, product: ProductInput, settings: CreativeSettings) -> CopyResult:
        if self.demo:
            return CopyResult(demo_copy(product, settings), "demo")
        schema = prompts.build_schema(settings.platforms)
        user = prompts.build_user_prompt(product, settings)
        res = self._call(prompts.SYSTEM_PROMPT, user, schema)
        try:
            copy = _validate(res.data, settings.platforms)
        except AppError as e:
            if not e.retryable:
                raise
            log.warning("invalid model output (%s); repairing once", e.code)
            res = self._call(prompts.SYSTEM_PROMPT, user + f"\n\nYour previous reply had a problem: {e.message}. "
                             "Return the COMPLETE JSON again with every field filled using only the facts.", schema)
            copy = _validate(res.data, settings.platforms)
        copy = self._post_check(copy, product)
        return CopyResult(copy, f"ollama:{res.model}", res.usage | {"latency_ms": res.latency_ms})

    def regenerate(self, current: CopyOutput, product: ProductInput, settings: CreativeSettings, *,
                   section: str | None, tone: Tone | None, instructions: str | None) -> CopyResult:
        settings = settings.model_copy(update={"tone": tone or settings.tone})
        if section is None:
            return self.generate(product, settings)
        if section.startswith("platform:"):
            try:
                Platform(section.split(":", 1)[1])
            except ValueError:
                raise AppError("bad_section", f"Unknown platform section '{section}'.")
        elif section not in prompts.CORE_FIELDS:
            raise AppError("bad_section", f"Unknown section '{section}'.")
        if self.demo:
            patch = demo_section(product, settings, section)
            usage = {}
            source = "demo"
        else:
            schema = prompts.build_schema(settings.platforms, section=section)
            user = prompts.build_user_prompt(product, settings, section=section, current=current, instructions=instructions)
            res = self._call(prompts.SYSTEM_PROMPT, user, schema)
            patch, usage, source = res.data, res.usage | {"latency_ms": res.latency_ms}, f"ollama:{res.model}"
        merged = current.model_copy(deep=True)
        if section.startswith("platform:"):
            key = section.split(":", 1)[1]
            spec = prompts.PLATFORM_FIELDS[Platform(key)]
            fields = patch.get(key) or {}
            norm = normalize({"platform_outputs": {key: fields}})["platform_outputs"].get(key, {})
            if not any(norm.values()):
                raise AppError("llm_incomplete_output", "The model returned nothing for that section.", retryable=True, status=502)
            merged.platform_outputs[key] = norm
        else:
            norm = normalize({section: patch.get(section)})
            val = norm[section]
            if val in ("", [], None):
                raise AppError("llm_incomplete_output", "The model returned nothing for that section.", retryable=True, status=502)
            data = merged.model_dump()
            data[section] = val
            merged = CopyOutput.model_validate(data)
        return CopyResult(self._post_check(merged, product), source, usage)

    @staticmethod
    def _post_check(copy: CopyOutput, product: ProductInput) -> CopyOutput:
        hits = forbidden_hits(copy, product.forbidden_words)
        flagged = [c for c in copy.claims_requiring_review if not c.startswith("Forbidden word used:")]
        flagged += [f"Forbidden word used: {w}" for w in hits]
        return copy.model_copy(update={"claims_requiring_review": flagged})
