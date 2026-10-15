import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
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


PLACEHOLDER = re.compile(r"\{[A-Za-z_]+\}|\[[A-Za-z_ ]+\]")


def _strip_placeholders(v):
    if isinstance(v, str):
        return re.sub(r"\s{2,}", " ", PLACEHOLDER.sub("", v)).strip()
    if isinstance(v, list):
        return [_strip_placeholders(x) for x in v]
    if isinstance(v, dict):
        return {k: _strip_placeholders(x) for k, x in v.items()}
    return v


def _validate(data: dict, platforms: list[Platform], *, strict: bool = True) -> CopyOutput:
    """strict=True: template placeholders are an error (triggers one repair). strict=False: strip them and flag."""
    had_placeholder = bool(PLACEHOLDER.search(json.dumps(data)))
    if had_placeholder and not strict:
        data = _strip_placeholders(data)
    cleaned = normalize(data)
    cleaned.setdefault("platform_outputs", {})
    try:
        copy = CopyOutput.model_validate(cleaned)
    except ValidationError as e:
        raise AppError("llm_invalid_output", f"The model's output didn't match the expected format: {e.error_count()} problems.",
                       retryable=True, status=502)
    if strict and PLACEHOLDER.search(copy.model_dump_json()):
        raise AppError("llm_placeholder_output", "The model left template placeholders in its output.",
                       retryable=True, status=502)
    empty = [f for f in REQUIRED_NONEMPTY if not getattr(copy, f).strip()]
    empty += [f"platform_outputs.{p.value}" for p in platforms if not any(copy.platform_outputs.get(p.value, {}).values())]
    if empty:
        err = AppError("llm_incomplete_output", "The model's output was missing: " + ", ".join(empty),
                       retryable=True, status=502)
        err.missing = empty
        raise err
    if had_placeholder and not strict:
        copy.claims_requiring_review.append(
            "The model left a template placeholder (like [Store Name]); it was removed. Re-read the copy around where it may have been.")
    return copy


def forbidden_hits(copy: CopyOutput, words: list[str]) -> list[str]:
    if not words:
        return []
    text = copy.model_dump_json().lower()
    return [w for w in words if re.search(rf"(?<!\w){re.escape(w.lower())}(?!\w)", text)]


# Claims a model likes to add. If one shows up in the copy but nowhere in the seller's own facts, flag it.
RISKY = ["eco-friendly", "organic", "natural", "vegan", "hypoallergenic", "certified", "handmade", "waterproof",
         "guarantee", "guaranteed", "best", "#1", "premium", "healthy", "clinically", "award", "bestseller",
         "limited edition", "sale", "discount", "free shipping", "kids", "children", "women", "men", "girls", "boys",
         "perfect", "delicious", "durable", "comfortable", "lifetime",
         # embellishments found by an independent audit of a fine-tuned model: invented urgency, occasions and audiences
         "available now", "in stock", "while supplies last", "gift idea", "gift ideas", "birthday", "holiday", "anniversary", "wedding"]
# Occasion words are fine when the seller says the product is for gifting at all.
GIFT_TERMS = {"gift idea", "gift ideas", "birthday", "holiday", "anniversary", "wedding"}


def risky_terms(copy: CopyOutput, product: ProductInput) -> list[str]:
    facts = " ".join(filter(None, [product.name, product.summary, product.materials, product.dimensions, product.audience,
                                   product.brand_voice, product.care_instructions, product.extra_notes,
                                   *product.features, *product.benefits])).lower()
    text = copy.model_dump_json(exclude={"claims_requiring_review", "missing_information"}).lower()
    pat = lambda w: re.compile(rf"(?<![\w-]){re.escape(w)}(?![\w-])")
    return [w for w in RISKY if pat(w).search(text) and not pat(w).search(facts) and not (w in GIFT_TERMS and "gift" in facts)]


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

    def _chunks(self, product, settings, note: str = ""):
        """Independent pieces of the kit. Each is a small JSON generation, so they run concurrently."""
        jobs = [(f"core:{n}", prompts.build_fields_schema(keys),
                 prompts.build_user_prompt(product, settings, fields=keys) + note)
                for n, keys in enumerate(prompts.CORE_CHUNKS)]
        for p in settings.platforms:
            sec = f"platform:{p.value}"
            jobs.append((sec, prompts.build_schema(settings.platforms, section=sec),
                         prompts.build_user_prompt(product, settings, section=sec) + note))
        return jobs

    def _run(self, jobs, on_progress=None):
        """Run chunks in parallel (Ollama serves them together when OLLAMA_NUM_PARALLEL > 1).
        on_progress(results_so_far, total) fires as each chunk finishes so the UI can show partial copy."""
        results: dict = {}
        with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
            futs = {pool.submit(self._call, prompts.SYSTEM_PROMPT, j[2], j[1]): j[0] for j in jobs}
            for f in as_completed(futs):
                results[futs[f]] = f.result()
                if on_progress:
                    on_progress(dict(results), len(jobs))
        return results

    def _partial(self, results: dict) -> CopyOutput | None:
        """Best-effort copy from the chunks finished so far (not validated; shown read-only until complete)."""
        try:
            data, _, _ = self._merge(results)
            return CopyOutput.model_validate(normalize(_strip_placeholders(data)))
        except Exception:  # noqa: BLE001 - a partial view must never break the real run
            return None

    @staticmethod
    def _merge(results: dict):
        data: dict = {"platform_outputs": {}}
        usage = {"prompt_tokens": 0, "completion_tokens": 0, "latency_ms": 0, "chunks": len(results)}
        for name, r in results.items():
            if name.startswith("core:"):
                data.update(r.data)
            else:
                key = name.split(":", 1)[1]
                data["platform_outputs"][key] = r.data.get(key) or {}
            usage["prompt_tokens"] += r.usage.get("prompt_tokens") or 0
            usage["completion_tokens"] += r.usage.get("completion_tokens") or 0
            usage["latency_ms"] = max(usage["latency_ms"], r.latency_ms)
        return data, usage, next(iter(results.values())).model

    @staticmethod
    def _chunks_for(missing: list[str]) -> set[str]:
        out = set()
        for m in missing:
            if m.startswith("platform_outputs."):
                out.add("platform:" + m.split(".", 1)[1])
            else:
                out.update(f"core:{n}" for n, keys in enumerate(prompts.CORE_CHUNKS) if m in keys)
        return out

    def generate(self, product: ProductInput, settings: CreativeSettings, on_progress=None) -> CopyResult:
        """on_progress(partial_copy, done, total) is called as parallel parts finish."""
        if self.demo:
            return CopyResult(demo_copy(product, settings), "demo")
        jobs = self._chunks(product, settings)
        cb = None
        if on_progress:
            def cb(done_results, total):
                partial = self._partial(done_results)
                if partial is not None:
                    on_progress(partial, len(done_results), total)
        results = self._run(jobs, cb)
        data, usage, model = self._merge(results)
        try:
            copy = _validate(data, settings.platforms, strict=False)  # placeholders are stripped + flagged, never a re-run
        except AppError as e:
            if not e.retryable:
                raise
            log.warning("invalid model output (%s); redoing only the failed parts", e.code)
            redo = self._chunks_for(getattr(e, "missing", [])) or {j[0] for j in jobs}
            retry_jobs = [j for j in self._chunks(product, settings, f"\n\nA previous attempt had a problem: {e.message}. "
                                                  "Fill every field using only the facts.") if j[0] in redo]
            results.update(self._run(retry_jobs))
            data, usage, model = self._merge(results)
            copy = _validate(data, settings.platforms, strict=False)
        copy = self._post_check(copy, product)
        return CopyResult(copy, f"ollama:{model}", usage)

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
        flagged = [c for c in copy.claims_requiring_review if not c.startswith(("Forbidden word used:", "Not in your facts:"))]
        flagged += [f"Forbidden word used: {w}" for w in hits]
        flagged += [f"Not in your facts: \"{w}\". Remove it unless it's true." for w in risky_terms(copy, product)]
        return copy.model_copy(update={"claims_requiring_review": flagged})
